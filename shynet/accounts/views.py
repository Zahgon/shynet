"""Account views.

Login, logout, sign-up, email management, email confirmation and the password
change/set/reset flows. Each view renders the same template, under the same
name, that the account templates already provide.
"""

from flask import (
    Blueprint,
    session,
    abort,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, select

from core.models import User, _default_uuid
from shynet import messages, settings, timezone
from shynet.extensions import db

from .adapter import get_adapter, is_open_for_signup
from .forms import (
    AddEmailForm,
    ChangePasswordForm,
    LoginForm,
    ResetPasswordForm,
    ResetPasswordKeyForm,
    SetPasswordForm,
    SignupForm,
)
from .models import EmailAddress, EmailConfirmation
from .utils import (
    REDIRECT_FIELD_NAME,
    get_login_redirect_url,
    get_redirect_field_value,
    load_password_reset_token,
    make_password_reset_token,
)

accounts = Blueprint("accounts", __name__)


def _start_session():
    """Discard any pre-existing session before signing a user in.

    Cookie sessions have no server-side identifier to cycle, so the equivalent
    of rotating the session key is to drop whatever was there first; that stops
    a planted session cookie from surviving authentication.
    """
    session.clear()
    session.permanent = True


def _flash_message(template_name, level=messages.INFO, **context):
    message = render_template(f"account/messages/{template_name}", **context).strip()
    if message:
        messages.add_message(level, message)


def _redirect_context():
    return {
        "redirect_field_name": REDIRECT_FIELD_NAME,
        "redirect_field_value": get_redirect_field_value(),
    }


def _send_email_confirmation(user, email_address):
    confirmation = EmailConfirmation.create(email_address)
    confirmation.sent = timezone.now()
    db.session.add(confirmation)
    db.session.commit()
    activate_url = url_for(
        "accounts.confirm_email", key=confirmation.key, _external=True
    )
    get_adapter().send_mail(
        "account/email/email_confirmation",
        email_address.email,
        {
            "user": user,
            "activate_url": activate_url,
            "current_site": request.site,
            "key": confirmation.key,
        },
    )
    _flash_message(
        "email_confirmation_sent.txt", messages.INFO, email=email_address.email
    )
    return confirmation


def _primary_email(user):
    return db.session.scalar(
        select(EmailAddress).where(
            EmailAddress.user_id == user.id, EmailAddress.primary.is_(True)
        )
    ) or db.session.scalar(
        select(EmailAddress).where(EmailAddress.user_id == user.id)
    )


def _has_verified_email(user):
    return bool(
        db.session.scalar(
            select(func.count())
            .select_from(EmailAddress)
            .where(
                EmailAddress.user_id == user.id, EmailAddress.verified.is_(True)
            )
        )
    )


@accounts.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = form.user
        if not user.is_active:
            return redirect(url_for("accounts.inactive"))
        if settings.ACCOUNT_EMAIL_VERIFICATION == "mandatory" and not _has_verified_email(
            user
        ):
            email_address = _primary_email(user)
            if email_address is not None:
                _send_email_confirmation(user, email_address)
            return redirect(url_for("accounts.email_verification_sent"))
        _start_session()
        login_user(user, remember=bool(form.remember.data))
        user.last_login = timezone.now()
        db.session.add(user)
        db.session.commit()
        _flash_message("logged_in.txt", messages.SUCCESS, user=user)
        return redirect(get_login_redirect_url())
    return render_template(
        "account/login.html",
        form=form,
        signup_url=url_for("accounts.signup"),
        login_url=url_for("accounts.login"),
        **_redirect_context(),
    )


@accounts.route("/logout/", methods=["GET", "POST"])
def logout():
    if request.method == "POST":
        if current_user.is_authenticated:
            logout_user()
            session.clear()
            _flash_message("logged_out.txt", messages.SUCCESS)
        return redirect(get_login_redirect_url() or "/")
    return render_template("account/logout.html", **_redirect_context())


@accounts.route("/signup/", methods=["GET", "POST"])
def signup():
    if not is_open_for_signup():
        return render_template("account/signup_closed.html")
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=_default_uuid(), email=form.email.data)
        user.set_password(form.password1.data)
        db.session.add(user)
        db.session.commit()

        email_address = EmailAddress(
            user_id=user.id, email=form.email.data, verified=False, primary=True
        )
        db.session.add(email_address)
        db.session.commit()

        if settings.ACCOUNT_EMAIL_VERIFICATION == "none":
            _start_session()
            login_user(user)
            _flash_message("logged_in.txt", messages.SUCCESS, user=user)
            return redirect(get_login_redirect_url())

        _send_email_confirmation(user, email_address)
        if settings.ACCOUNT_EMAIL_VERIFICATION == "mandatory":
            return redirect(url_for("accounts.email_verification_sent"))
        _start_session()
        login_user(user)
        _flash_message("logged_in.txt", messages.SUCCESS, user=user)
        return redirect(get_login_redirect_url())
    return render_template(
        "account/signup.html",
        form=form,
        login_url=url_for("accounts.login"),
        **_redirect_context(),
    )


@accounts.route("/inactive/")
def inactive():
    return render_template("account/account_inactive.html")


@accounts.route("/confirm-email/")
def email_verification_sent():
    return render_template("account/verification_sent.html")


@accounts.route("/confirm-email/<key>/", methods=["GET", "POST"])
def confirm_email(key):
    confirmation = EmailConfirmation.from_key(key)
    if request.method == "POST":
        if confirmation is None:
            abort(404)
        email_address = confirmation.confirm()
        _flash_message(
            "email_confirmed.txt", messages.SUCCESS, email=email_address.email
        )
        if current_user.is_authenticated:
            return redirect(url_for("accounts.email"))
        return redirect(url_for("accounts.login"))
    return render_template("account/email_confirm.html", confirmation=confirmation)


@accounts.route("/email/", methods=["GET", "POST"])
@login_required
def email():
    form = AddEmailForm(user=current_user)
    if request.method == "POST":
        if "action_add" in request.form:
            if form.validate_on_submit():
                email_address = EmailAddress(
                    user_id=current_user.id,
                    email=form.email.data,
                    verified=False,
                    primary=False,
                )
                db.session.add(email_address)
                db.session.commit()
                _send_email_confirmation(current_user, email_address)
                return redirect(url_for("accounts.email"))
        else:
            selected = request.form.get("email")
            email_address = db.session.scalar(
                select(EmailAddress).where(
                    EmailAddress.user_id == current_user.id,
                    EmailAddress.email == selected,
                )
            )
            if email_address is not None:
                if "action_send" in request.form:
                    _send_email_confirmation(current_user, email_address)
                elif "action_primary" in request.form:
                    if not email_address.verified:
                        _flash_message(
                            "unverified_primary_email.txt", messages.ERROR
                        )
                    else:
                        email_address.set_as_primary()
                        _flash_message("primary_email_set.txt", messages.SUCCESS)
                elif "action_remove" in request.form:
                    if email_address.primary:
                        _flash_message(
                            "cannot_delete_primary_email.txt",
                            messages.ERROR,
                            email=email_address.email,
                        )
                    else:
                        db.session.delete(email_address)
                        db.session.commit()
                        _flash_message(
                            "email_deleted.txt",
                            messages.SUCCESS,
                            email=email_address.email,
                        )
                return redirect(url_for("accounts.email"))
    return render_template("account/email.html", form=form)


@accounts.route("/password/change/", methods=["GET", "POST"])
@login_required
def change_password():
    if not current_user.has_usable_password():
        return redirect(url_for("accounts.set_password"))
    form = ChangePasswordForm(user=current_user)
    if form.validate_on_submit():
        current_user.set_password(form.password1.data)
        db.session.add(current_user)
        db.session.commit()
        _flash_message("password_changed.txt", messages.SUCCESS)
        return redirect(url_for("accounts.change_password"))
    return render_template("account/password_change.html", form=form)


@accounts.route("/password/set/", methods=["GET", "POST"])
@login_required
def set_password():
    if current_user.has_usable_password():
        return redirect(url_for("accounts.change_password"))
    form = SetPasswordForm(user=current_user)
    if form.validate_on_submit():
        current_user.set_password(form.password1.data)
        db.session.add(current_user)
        db.session.commit()
        _flash_message("password_set.txt", messages.SUCCESS)
        return redirect(url_for("accounts.change_password"))
    return render_template("account/password_set.html", form=form)


@accounts.route("/password/reset/", methods=["GET", "POST"])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        for user in form.users:
            token = make_password_reset_token(user)
            password_reset_url = url_for(
                "accounts.reset_password_from_key", key=token, _external=True
            )
            get_adapter().send_mail(
                "account/email/password_reset_key",
                user.email,
                {
                    "user": user,
                    "password_reset_url": password_reset_url,
                    "current_site": request.site,
                },
            )
        return redirect(url_for("accounts.reset_password_done"))
    return render_template("account/password_reset.html", form=form)


@accounts.route("/password/reset/done/")
def reset_password_done():
    return render_template("account/password_reset_done.html")


@accounts.route("/password/reset/key/<key>/", methods=["GET", "POST"])
def reset_password_from_key(key):
    user = load_password_reset_token(key)
    if user is None:
        return render_template(
            "account/password_reset_from_key.html", token_fail=True, form=None
        )
    form = ResetPasswordKeyForm(user=user)
    if form.validate_on_submit():
        user.set_password(form.password1.data)
        db.session.add(user)
        db.session.commit()
        _flash_message("password_changed.txt", messages.SUCCESS)
        return redirect(url_for("accounts.reset_password_from_key_done"))
    return render_template(
        "account/password_reset_from_key.html",
        token_fail=False,
        form=form,
        action_url=url_for("accounts.reset_password_from_key", key=key),
    )


@accounts.route("/password/reset/key/done/")
def reset_password_from_key_done():
    return render_template("account/password_reset_from_key_done.html")
