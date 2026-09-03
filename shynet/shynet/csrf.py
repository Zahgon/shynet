"""CSRF protection.

Flask-WTF's `CSRFProtect`, extended with support for
`settings.CSRF_TRUSTED_ORIGINS` so that the Origin/Referer check behaves the way
Shynet's configuration expects.
"""

from urllib.parse import urlsplit

from flask import current_app, request
from flask_wtf.csrf import CSRFError
from flask_wtf.csrf import CSRFProtect as BaseCSRFProtect


class CSRFProtect(BaseCSRFProtect):
    def init_app(self, app):
        # The strict SSL referer check is reimplemented below so that
        # CSRF_TRUSTED_ORIGINS is honoured.
        app.config["WTF_CSRF_SSL_STRICT"] = False
        return super().init_app(app)

    def protect(self):
        if request.method in current_app.config["WTF_CSRF_METHODS"]:
            self._check_origin()
        return super().protect()

    def _check_origin(self):
        if not request.is_secure:
            return

        trusted = list(current_app.config.get("CSRF_TRUSTED_ORIGINS") or [])
        good_origin = f"{request.scheme}://{request.host}"

        origin = request.headers.get("Origin")
        if origin:
            if origin == good_origin or origin in trusted:
                return
            self._error_response(
                f"Origin checking failed - {origin} does not match any trusted origins."
            )

        referrer = request.referrer
        if not referrer:
            self._error_response("The referrer header is missing.")

        parts = urlsplit(referrer)
        if not parts.scheme or not parts.netloc:
            self._error_response(f"The referrer header is malformed - {referrer}.")

        referrer_origin = f"{parts.scheme}://{parts.netloc}"
        if referrer_origin == good_origin or referrer_origin in trusted:
            return

        self._error_response(
            f"Referrer checking failed - {referrer} does not match any trusted origins."
        )

    def _error_response(self, reason):
        raise CSRFError(reason)
