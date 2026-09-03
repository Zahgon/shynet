"""Object-level permissions.

A small predicate registry: `@predicate` wraps a function so that predicates can
be combined with `|` and `&`, `add_perm` registers a rule under a permission
name, and `has_perm` evaluates it. Predicates are called with `(user)` or
`(user, obj)` depending on how many arguments they accept.
"""

import inspect


class Predicate:
    def __init__(self, func, name=None):
        self.func = func
        self.name = name or getattr(func, "__name__", "predicate")
        self.num_args = len(inspect.signature(func).parameters)

    def __call__(self, user, obj=None):
        if self.num_args >= 2:
            if obj is None:
                return False
            return bool(self.func(user, obj))
        return bool(self.func(user))

    def __or__(self, other):
        return Predicate(
            lambda user, obj=None: self(user, obj) or other(user, obj),
            name=f"({self.name} | {other.name})",
        )

    def __and__(self, other):
        return Predicate(
            lambda user, obj=None: self(user, obj) and other(user, obj),
            name=f"({self.name} & {other.name})",
        )

    def __invert__(self):
        return Predicate(
            lambda user, obj=None: not self(user, obj), name=f"~{self.name}"
        )


def predicate(func):
    """Turn a plain function into a combinable `Predicate`."""
    if isinstance(func, Predicate):
        return func
    # Two-argument lambdas built by __or__/__and__ take (user, obj=None).
    wrapped = Predicate(func)
    return wrapped


_permissions = {}


def add_perm(name, pred):
    _permissions[name] = pred


def remove_perm(name):
    _permissions.pop(name, None)


def perm_exists(name):
    return name in _permissions


def has_perm(name, user=None, obj=None):
    """Whether `user` holds `name` for `obj`.

    Active superusers hold every permission; otherwise the registered rule
    decides. Anonymous users are passed to the rule rather than rejected
    outright, so a rule that grants a permission to everyone still applies.
    """
    if user is None:
        return False
    if getattr(user, "is_active", False) and getattr(user, "is_superuser", False):
        return True
    pred = _permissions.get(name)
    if pred is None:
        return False
    if isinstance(pred, Predicate):
        return pred(user, obj)
    return bool(pred(user, obj))


def autodiscover():
    """Import every installed app's `rules` module, registering its permissions."""
    import importlib

    from . import settings

    for app in settings.INSTALLED_APPS:
        try:
            importlib.import_module(f"{app}.rules")
        except ModuleNotFoundError:
            continue
