"""Password validators.

The four validators listed in `settings.AUTH_PASSWORD_VALIDATORS`, ported so
that sign-up, password change, password set and password reset all apply the
same rules they did before. `CommonPasswordValidator` reads the bundled
`common-passwords.txt.gz` word list.
"""

import gzip
import os
import re
from difflib import SequenceMatcher

from flask_babel import gettext as _

from shynet.exceptions import ValidationError

DEFAULT_PASSWORD_LIST_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "common-passwords.txt.gz"
)


def exceeds_maximum_length_ratio(password, max_similarity, value):
    """Whether `password` can be ruled out as too similar without comparing."""
    pwd_len = len(password)
    length_bound_similarity = max_similarity / 2 * pwd_len
    value_len = len(value)
    return pwd_len >= 10 * value_len and value_len < length_bound_similarity


class MinimumLengthValidator:
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _(
                    "This password is too short. It must contain at least "
                    "%(min_length)d characters."
                )
                % {"min_length": self.min_length},
                code="password_too_short",
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(min_length)d characters."
        ) % {"min_length": self.min_length}


class UserAttributeSimilarityValidator:
    DEFAULT_USER_ATTRIBUTES = ("username", "first_name", "last_name", "email")

    def __init__(self, user_attributes=DEFAULT_USER_ATTRIBUTES, max_similarity=0.7):
        self.user_attributes = user_attributes
        self.max_similarity = max_similarity

    def validate(self, password, user=None):
        if not user:
            return

        password = password.lower()
        for attribute_name in self.user_attributes:
            value = getattr(user, attribute_name, None)
            if not value or not isinstance(value, str):
                continue
            value_lower = value.lower()
            value_parts = re.split(r"\W+", value_lower) + [value_lower]
            for value_part in value_parts:
                if exceeds_maximum_length_ratio(
                    password, self.max_similarity, value_part
                ):
                    continue
                if (
                    SequenceMatcher(a=password, b=value_part).quick_ratio()
                    >= self.max_similarity
                ):
                    verbose_name = attribute_name.replace("_", " ")
                    raise ValidationError(
                        _("The password is too similar to the %(verbose_name)s.")
                        % {"verbose_name": verbose_name},
                        code="password_too_similar",
                    )

    def get_help_text(self):
        return _("Your password can't be too similar to your other personal information.")


class CommonPasswordValidator:
    def __init__(self, password_list_path=DEFAULT_PASSWORD_LIST_PATH):
        self.password_list_path = password_list_path
        try:
            with gzip.open(self.password_list_path, "rt", encoding="utf-8") as f:
                self.passwords = {x.strip() for x in f}
        except OSError:
            with open(self.password_list_path, encoding="utf-8") as f:
                self.passwords = {x.strip() for x in f}

    def validate(self, password, user=None):
        if password.lower().strip() in self.passwords:
            raise ValidationError(
                _("This password is too common."), code="password_too_common"
            )

    def get_help_text(self):
        return _("Your password can't be a commonly used password.")


class NumericPasswordValidator:
    def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError(
                _("This password is entirely numeric."), code="password_entirely_numeric"
            )

    def get_help_text(self):
        return _("Your password can't be entirely numeric.")


_validators = None


def get_password_validators():
    global _validators
    if _validators is None:
        from shynet import settings

        _validators = []
        for config in settings.AUTH_PASSWORD_VALIDATORS:
            module_name, class_name = config["NAME"].rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            _validators.append(
                getattr(module, class_name)(**config.get("OPTIONS", {}))
            )
    return _validators


def validate_password(password, user=None, password_validators=None):
    """Run every configured validator, collecting all failures."""
    errors = []
    if password_validators is None:
        password_validators = get_password_validators()
    for validator in password_validators:
        try:
            validator.validate(password, user)
        except ValidationError as error:
            errors.extend(error.messages)
    if errors:
        raise ValidationError(errors)


def password_validators_help_texts(password_validators=None):
    if password_validators is None:
        password_validators = get_password_validators()
    return [validator.get_help_text() for validator in password_validators]
