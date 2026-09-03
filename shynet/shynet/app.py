"""Application factory for Shynet."""

import os

from flask import Flask
from whitenoise import WhiteNoise

from . import commands, logs, middleware, rules, settings, templating
from .json import ShynetJSONProvider
from .extensions import (
    babel,
    cache,
    csrf,
    db,
    login_manager,
    mail,
    make_admin,
    migrate,
)


def create_app(config_overrides=None):
    logs.configure(settings.LOGGING)

    app = Flask(
        "shynet",
        static_folder=None,  # served by `shynet.staticfiles`
        template_folder=os.path.join(settings.BASE_DIR, "shynet", "templates"),
    )
    app.json = ShynetJSONProvider(app)
    app.config.update(settings.as_flask_config())
    if config_overrides:
        app.config.update(config_overrides)

    _init_extensions(app)
    _init_blueprints(app)
    _init_admin(app)

    middleware.register(app)
    templating.init_app(app)
    commands.register(app)
    rules.autodiscover()
    _run_app_configs()

    _init_whitenoise(app)

    return app


def _init_extensions(app):
    db.init_app(app)
    migrate.init_app(
        app, db, directory=os.path.join(settings.BASE_DIR, "migrations")
    )
    cache.init_app(app)
    mail.init_app(app)
    babel.init_app(app, locale_selector=_select_locale)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "accounts.login"
    login_manager.login_message = None

    from core.models import AnonymousUser, User

    login_manager.anonymous_user = AnonymousUser

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    if settings.DEBUG:
        try:
            from flask_debugtoolbar import DebugToolbarExtension

            DebugToolbarExtension(app)
        except ImportError:  # pragma: no cover - development only
            pass


def _select_locale():
    """The active locale; Shynet serves a single configured language."""
    return settings.LANGUAGE_CODE.replace("-", "_")


def _init_blueprints(app):
    from .urls import register_blueprints

    register_blueprints(app)


def _init_admin(app):
    """Register each installed app's admin views."""
    import importlib

    from core.admin import ShynetAdminIndexView

    admin = make_admin(index_view=ShynetAdminIndexView())
    admin.init_app(app)
    for app_name in settings.INSTALLED_APPS:
        try:
            module = importlib.import_module(f"{app_name}.admin")
        except ModuleNotFoundError:
            continue
        register = getattr(module, "register_admin", None)
        if register is not None:
            register(admin)


def _run_app_configs():
    """Call each installed app's config `ready()` hook."""
    import importlib

    for app_name in settings.INSTALLED_APPS:
        try:
            module = importlib.import_module(f"{app_name}.apps")
        except ModuleNotFoundError:
            continue
        for attribute in vars(module).values():
            if (
                isinstance(attribute, type)
                and getattr(attribute, "name", None) == app_name
                and hasattr(attribute, "ready")
            ):
                attribute().ready()


def _init_whitenoise(app):
    static_root = os.path.join(settings.BASE_DIR, settings.STATIC_ROOT)
    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=static_root if os.path.isdir(static_root) else None,
        prefix=settings.STATIC_URL,
        autorefresh=settings.DEBUG,
    )
