"""The static file view must not serve anything outside the static roots."""

import pytest

TRAVERSALS = [
    "/static/%2e%2e/%2e%2e/shynet/settings.py",
    "/static/%2e%2e/%2e%2e/%2e%2e/TEMPLATE.env",
    "/static/" + "%2e%2e/" * 12 + "etc/passwd",
    "/static/../../shynet/settings.py",
    "/static/..%2f..%2fshynet/settings.py",
    "/static/%2e%2e%2f%2e%2e%2fTEMPLATE.env",
    "/static/dashboard/../../../TEMPLATE.env",
    # The npm finder's glob patterns match a directory prefix, so they need
    # the same containment check as the app directories.
    "/static/inter-ui/Inter (web)/" + "%2e%2e/" * 3 + "TEMPLATE.env",
    "/static/flag-icon-css/flags/" + "%2e%2e/" * 12 + "etc/passwd",
]


@pytest.mark.parametrize("path", TRAVERSALS)
def test_static_view_rejects_path_traversal(client, path):
    """
    GIVEN: A request for a static file that points outside the static roots
    WHEN: The static view handles it
    THEN: It should not serve the file
    """
    response = client.get(path)

    assert response.status_code != 200


def test_static_view_serves_app_assets(client):
    """
    GIVEN: A request for a file in an app's static directory
    WHEN: The static view handles it
    THEN: It should serve the file
    """
    response = client.get("/static/dashboard/css/global.css")

    assert response.status_code == 200
    assert b".limited-height" in response.data
