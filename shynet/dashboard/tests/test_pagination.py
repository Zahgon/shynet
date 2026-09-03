"""An out-of-range or malformed page number should 404, not silently clamp."""

import pytest

from core.factories import UserFactory


@pytest.fixture()
def logged_in_client(app, client):
    user = UserFactory()
    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True
    return client


@pytest.mark.parametrize(
    "query,expected",
    [
        ("", 200),
        ("?page=1", 200),
        ("?page=last", 200),
        ("?page=999", 404),
        ("?page=0", 404),
        ("?page=-1", 404),
        ("?page=abc", 404),
    ],
)
def test_dashboard_pagination_bounds(logged_in_client, query, expected):
    response = logged_in_client.get("/dashboard/" + query)

    assert response.status_code == expected
