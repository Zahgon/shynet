"""Regression tests for the access-control helpers written for this project.

These have no counterpart in the previous framework, so they are covered here
directly rather than through the views that use them.
"""

import pytest

from shynet.middleware import validate_host
from shynet.rules import has_perm


class _User:
    def __init__(self, is_active=True, is_superuser=False):
        self.is_active = is_active
        self.is_superuser = is_superuser


@pytest.mark.parametrize(
    "host,allowed,expected",
    [
        ("example.com", ["example.com"], True),
        ("EXAMPLE.com", ["example.com"], True),
        ("example.com.", ["example.com"], True),
        ("example.com:8080", ["example.com"], True),
        ("evil.com", ["example.com"], False),
        ("sub.example.com", [".example.com"], True),
        ("example.com", [".example.com"], True),
        ("evil.example.com.attacker.net", [".example.com"], False),
        ("[::1]:8080", ["[::1]"], True),
        ("anything", ["*"], True),
        # Glob patterns are not supported, so a mistyped pattern fails closed.
        ("sub.example.com", ["*.example.com"], False),
        ("exampleXcom", ["example?com"], False),
        ("malformed_host!", ["malformed_host!"], False),
    ],
)
def test_validate_host(host, allowed, expected):
    assert validate_host(host, allowed) is expected


@pytest.mark.parametrize(
    "target,expected",
    [
        ("/dashboard/", True),
        ("  /dashboard/  ", True),
        ("http://localhost/dashboard/", True),
        ("//evil.example/", False),
        ("///evil.example/", False),
        ("\\\\evil.example/", False),
        # Browsers read a backslash as a slash, making this protocol-relative.
        ("/\\evil.example/", False),
        ("https://evil.example/", False),
        ("javascript:alert(1)", False),
        ("\x01/dashboard/", False),
        ("", False),
        (None, False),
    ],
)
def test_is_safe_url(app, target, expected):
    """
    GIVEN: A `next` parameter
    WHEN: The login redirect target is validated
    THEN: Only same-host targets should be accepted
    """
    from accounts.utils import is_safe_url

    with app.test_request_context("/", base_url="http://localhost"):
        assert is_safe_url(target) is expected


def test_superuser_bypass_requires_an_active_account(app):
    """
    GIVEN: A superuser whose account has been deactivated
    WHEN: An object permission that holds no rule for them is checked
    THEN: The blanket superuser grant should not apply
    """
    assert has_perm("core.view_service", _User(is_active=True, is_superuser=True)) is True
    assert (
        has_perm("core.view_service", _User(is_active=False, is_superuser=True)) is False
    )


def test_rules_apply_independently_of_the_superuser_bypass(app):
    """
    GIVEN: A rule that grants a permission on its own terms
    WHEN: The permission is checked
    THEN: The rule should decide, whatever the superuser bypass did
    """
    # `is_service_creator` grants this to any superuser, active or not.
    assert has_perm("core.create_service", _User(is_active=False, is_superuser=True)) is True
    assert has_perm("core.create_service", _User(is_active=True, is_superuser=False)) is False


def test_unregistered_permission_is_denied(app):
    """
    GIVEN: A permission with no rule registered for it
    WHEN: It is checked for a regular user
    THEN: It should be denied
    """
    assert has_perm("core.does_not_exist", _User()) is False
