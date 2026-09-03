"""Account forms.

Direct replacements for the account forms the templates render through the
`a17t` filter: the same fields, labels and validation behaviour.
"""

from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm
from sqlalchemy import func, select
from wtforms import BooleanField, PasswordField, StringField
from wtforms.validators import DataRequired, Email, ValidationError

from core.models import User
from core.password_validation import validate_password
from shynet.exceptions import ValidationError as ShynetValidationError
from shynet.extensions import db

from .models import EmailAddress


def _check_password_rules(form, field, user=None):
    try:
        validate_password(field.data or "", user)
    except ShynetValidationError as error:
        raise ValidationError(" ".join(str(message) for message in error.messages))


class LoginForm(FlaskForm):
    login = StringField(_("E-mail address"), validators=[DataRequired(), Email()])
    password = PasswordField(_("Password"), validators=[DataRequired()])
    remember = BooleanField(_("Remember Me"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        user = db.session.scalar(
            select(User).where(func.lower(User.email) == self.login.data.lower())
        )
        if user is None or not user.check_password(self.password.data):
            self.password.errors = list(self.password.errors) + [
                str(
                    _(
                        "The e-mail address and/or password you specified are not correct."
                    )
                )
            ]
            return False
        self.user = user
        return True


class SignupForm(FlaskForm):
    email = StringField(_("E-mail address"), validators=[DataRequired(), Email()])
    password1 = PasswordField(_("Password"), validators=[DataRequired()])
    password2 = PasswordField(_("Password (again)"), validators=[DataRequired()])

    def validate_email(self, field):
        if EmailAddress.lookup(field.data) is not None or db.session.scalar(
            select(User).where(func.lower(User.email) == field.data.lower())
        ):
            raise ValidationError(
                str(
                    _(
                        "A user is already registered with this e-mail address."
                    )
                )
            )

    def validate_password1(self, field):
        _check_password_rules(self, field)

    def validate_password2(self, field):
        if self.password1.data != field.data:
            raise ValidationError(
                str(_("You must type the same password each time."))
            )


class AddEmailForm(FlaskForm):
    email = StringField(_("E-mail address"), validators=[DataRequired(), Email()])

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def validate_email(self, field):
        existing = EmailAddress.lookup(field.data)
        if existing is not None:
            if self.user is not None and existing.user_id == self.user.id:
                raise ValidationError(
                    str(_("This e-mail address is already associated with this account."))
                )
            raise ValidationError(
                str(_("A user is already registered with this e-mail address."))
            )


class ChangePasswordForm(FlaskForm):
    oldpassword = PasswordField(_("Current Password"), validators=[DataRequired()])
    password1 = PasswordField(_("New Password"), validators=[DataRequired()])
    password2 = PasswordField(_("New Password (again)"), validators=[DataRequired()])

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def validate_oldpassword(self, field):
        if self.user is None or not self.user.check_password(field.data):
            raise ValidationError(
                str(_("Please type your current password."))
            )

    def validate_password1(self, field):
        _check_password_rules(self, field, self.user)

    def validate_password2(self, field):
        if self.password1.data != field.data:
            raise ValidationError(str(_("You must type the same password each time.")))


class SetPasswordForm(FlaskForm):
    password1 = PasswordField(_("Password"), validators=[DataRequired()])
    password2 = PasswordField(_("Password (again)"), validators=[DataRequired()])

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def validate_password1(self, field):
        _check_password_rules(self, field, self.user)

    def validate_password2(self, field):
        if self.password1.data != field.data:
            raise ValidationError(str(_("You must type the same password each time.")))


class ResetPasswordForm(FlaskForm):
    email = StringField(_("E-mail address"), validators=[DataRequired(), Email()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.users = []

    def validate_email(self, field):
        user = db.session.scalar(
            select(User).where(func.lower(User.email) == field.data.lower())
        )
        if user is None:
            raise ValidationError(
                str(_("The e-mail address is not assigned to any user account."))
            )
        self.users = [user]


class ResetPasswordKeyForm(SetPasswordForm):
    pass
