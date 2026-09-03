"""Client IP extraction from the proxy headers."""

import pytest
from flask import request

CASES = [
    # The precedence order puts Cloudflare's header first.
    ({"CF-Connecting-IP": "9.9.9.9", "X-Forwarded-For": "8.8.8.8"}, ("9.9.9.9", True)),
    ({"X-Forwarded-For": "8.8.8.8, 10.0.0.1"}, ("8.8.8.8", True)),
    ({"X-Forwarded-For": "10.0.0.1, 8.8.4.4"}, ("8.8.4.4", True)),
    ({"X-Real-IP": "1.1.1.1"}, ("1.1.1.1", True)),
    # Ports are stripped, for both address families.
    ({"X-Forwarded-For": "1.2.3.4:5678"}, ("1.2.3.4", True)),
    ({"X-Forwarded-For": "[2001:4860:4860::8888]:443"}, ("2001:4860:4860::8888", True)),
    ({"X-Forwarded-For": "2001:4860:4860::8888"}, ("2001:4860:4860::8888", True)),
    # An IPv4-mapped address keeps its form and is classified by the address
    # it wraps, rather than being re-serialised into hextets.
    ({"X-Forwarded-For": "::ffff:8.8.8.8"}, ("::ffff:8.8.8.8", True)),
    ({"X-Forwarded-For": "::FFFF:8.8.8.8"}, ("::ffff:8.8.8.8", True)),
    ({"X-Forwarded-For": "::ffff:10.0.0.1"}, ("::ffff:10.0.0.1", False)),
    # Malformed entries are skipped, not fatal.
    ({"X-Forwarded-For": "not-an-ip, 8.8.8.8"}, ("8.8.8.8", True)),
    ({"X-Forwarded-For": "  , , 8.8.8.8 "}, ("8.8.8.8", True)),
    ({"X-Forwarded-For": "not-an-ip"}, (None, False)),
    # With nothing routable, a private address beats a loopback one.
    ({"X-Forwarded-For": "127.0.0.1, 10.0.0.5"}, ("10.0.0.5", False)),
    ({"X-Forwarded-For": "10.0.0.5, 127.0.0.1"}, ("10.0.0.5", False)),
]


@pytest.mark.parametrize("headers,expected", CASES)
def test_get_client_ip(app, headers, expected):
    from shynet.ipware import get_client_ip

    with app.test_request_context("/", headers=headers, environ_base={"REMOTE_ADDR": ""}):
        assert get_client_ip(request) == expected


def test_get_client_ip_falls_back_to_remote_addr(app):
    from shynet.ipware import get_client_ip

    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "127.0.0.1"}):
        assert get_client_ip(request) == ("127.0.0.1", False)
