"""Account helpers: redirect handling and password reset tokens."""

import unicodedata
from urllib.parse import urlparse

from flask import request, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from shynet import settings

REDIRECT_FIELD_NAME = "next"

VALID_REDIRECT_SCHEMES = ["http", "https"]


def get_redirect_field_value():
    return request.values.get(REDIRECT_FIELD_NAME, "")


def _has_allowed_host_and_scheme(url, allowed_hosts):
    if url.startswith("///"):
        return False
    try:
        url_info = urlparse(url)
    except ValueError:
        return False
    # A scheme with no host ("javascript:...") is never a local redirect.
    if not url_info.netloc and url_info.scheme:
        return False
    if unicodedata.category(url[0])[0] == "C":
        return False
    scheme = url_info.scheme
    if not url_info.scheme and url_info.netloc:
        # A protocol-relative URL; treat it as the browser would.
        scheme = "http"
    return (not url_info.netloc or url_info.netloc in allowed_hosts) and (
        not scheme or scheme in VALID_REDIRECT_SCHEMES
    )


def is_safe_url(target, allowed_hosts=None):
    """Only allow redirects that stay on this host.

    The URL is checked twice, the second time with backslashes rewritten as
    slashes, because browsers treat `/\evil.example` as protocol-relative.
    """
    if target is not None:
        target = target.strip()
    if not target:
        return False
    if allowed_hosts is None:
        allowed_hosts = {request.host}
    elif isinstance(allowed_hosts, str):
        allowed_hosts = {allowed_hosts}
    return _has_allowed_host_and_scheme(
        target, allowed_hosts
    ) and _has_allowed_host_and_scheme(target.replace("\\", "/"), allowed_hosts)


def get_login_redirect_url():
    target = get_redirect_field_value()
    if is_safe_url(target):
        return target
    return settings.LOGIN_REDIRECT_URL


def _serializer(salt):
    from flask import current_app

    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=salt)


def make_password_reset_token(user):
    """A signed token that also invalidates once the password changes."""
    return _serializer("shynet.password-reset").dumps(
        {"uid": user.id, "hash": (user.password or "")[-16:]}
    )


def load_password_reset_token(token):
    from core.models import User
    from shynet.extensions import db

    try:
        data = _serializer("shynet.password-reset").loads(
            token, max_age=settings.ACCOUNT_PASSWORD_RESET_EXPIRE_SECONDS
        )
    except (BadSignature, SignatureExpired):
        return None
    user = db.session.get(User, data.get("uid"))
    if user is None or (user.password or "")[-16:] != data.get("hash"):
        return None
    return user


def build_absolute_url(endpoint, **values):
    return url_for(endpoint, _external=True, **values)
