"""Request/response middleware.

These hooks replace the middleware stack Shynet used to configure: Host header
validation, the security headers, and attaching the current `Site` to the
request.
"""

import re

from flask import abort, request

from . import settings

# A hostname, optionally bracketed (IPv6) and optionally followed by a port.
HOST_VALIDATION_RE = re.compile(
    r"^([a-z0-9.-]+|\[[a-f0-9]*:[a-f0-9.:]+\])(:[0-9]+)?$"
)


def split_domain_port(host):
    """Split `host` into `(domain, port)`, or `("", "")` if it is malformed.

    The header is deliberately not stripped: trailing whitespace makes a host
    invalid rather than equivalent to the trimmed one.
    """
    host = (host or "").lower()
    if not HOST_VALIDATION_RE.match(host):
        return "", ""
    if host[-1] == "]":
        # An IPv6 literal with no port.
        return host, ""
    bits = host.rsplit(":", 1)
    domain, port = bits if len(bits) == 2 else (bits[0], "")
    return domain[:-1] if domain.endswith(".") else domain, port


def is_same_domain(host, pattern):
    """Whether `host` equals `pattern`, or is a subdomain of a `.pattern`."""
    if not pattern:
        return False
    pattern = pattern.lower()
    return (
        pattern[0] == "." and (host.endswith(pattern) or host == pattern[1:])
    ) or pattern == host


def validate_host(host, allowed_hosts):
    """True when `host` matches one of the ALLOWED_HOSTS patterns.

    Only an exact hostname or a leading-dot subdomain pattern matches; there is
    deliberately no glob support, so a mistyped pattern fails closed.
    """
    domain, _port = split_domain_port(host)
    if not domain:
        return False
    return any(
        pattern == "*" or is_same_domain(domain, pattern.strip())
        for pattern in allowed_hosts
    )


def register(app):
    @app.before_request
    def _validate_host():
        if not validate_host(request.host, app.config["ALLOWED_HOSTS"]):
            abort(400, f"Invalid HTTP_HOST header: {request.host!r}.")

    @app.before_request
    def _attach_current_site():
        from core.models import Site

        request.site = Site.get_current()

    @app.after_request
    def _cors_headers(response):
        """Add the cross-origin headers, for the tracking endpoints in particular."""
        origin = request.headers.get("Origin")
        if not origin:
            return response

        if settings.CORS_ALLOW_ALL_ORIGINS and not settings.CORS_ALLOW_CREDENTIALS:
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers.add("Vary", "Origin")

        if settings.CORS_ALLOW_CREDENTIALS:
            response.headers["Access-Control-Allow-Credentials"] = "true"

        if settings.CORS_EXPOSE_HEADERS:
            response.headers["Access-Control-Expose-Headers"] = ", ".join(
                settings.CORS_EXPOSE_HEADERS
            )

        if request.method == "OPTIONS":
            response.headers["Access-Control-Allow-Headers"] = ", ".join(
                settings.CORS_ALLOW_HEADERS
            )
            response.headers["Access-Control-Allow-Methods"] = ", ".join(
                settings.CORS_ALLOW_METHODS
            )
            if settings.CORS_PREFLIGHT_MAX_AGE:
                response.headers["Access-Control-Max-Age"] = str(
                    settings.CORS_PREFLIGHT_MAX_AGE
                )

        return response

    @app.after_request
    def _security_headers(response):
        if settings.SECURE_CONTENT_TYPE_NOSNIFF:
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
        if settings.SECURE_REFERRER_POLICY:
            response.headers.setdefault(
                "Referrer-Policy", settings.SECURE_REFERRER_POLICY
            )
        if settings.SECURE_CROSS_ORIGIN_OPENER_POLICY:
            response.headers.setdefault(
                "Cross-Origin-Opener-Policy",
                settings.SECURE_CROSS_ORIGIN_OPENER_POLICY,
            )
        if settings.X_FRAME_OPTIONS:
            response.headers.setdefault("X-Frame-Options", settings.X_FRAME_OPTIONS)
        return response
