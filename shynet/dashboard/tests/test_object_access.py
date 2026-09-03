"""A service that does not exist must 404, not report a permission failure."""

import uuid

import pytest

from core.factories import ServiceFactory, UserFactory


@pytest.fixture()
def owner_client(app, client):
    user = UserFactory(username="owner")
    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True
    client.service = ServiceFactory(owner=user)
    return client


@pytest.mark.parametrize(
    "template",
    [
        "/dashboard/service/{pk}/",
        "/dashboard/service/{pk}/manage/",
        "/dashboard/service/{pk}/delete/",
        "/dashboard/service/{pk}/sessions/",
        "/dashboard/service/{pk}/locations/",
    ],
)
def test_missing_service_returns_404(owner_client, template):
    response = owner_client.get(template.format(pk=uuid.uuid4()))

    assert response.status_code == 404


def test_malformed_uuid_returns_404(owner_client):
    response = owner_client.get("/dashboard/service/not-a-uuid/")

    assert response.status_code == 404


def test_owner_can_view_their_own_service(owner_client):
    response = owner_client.get(f"/dashboard/service/{owner_client.service.uuid}/")

    assert response.status_code == 200


def test_other_users_service_is_forbidden(app, client):
    stranger = UserFactory(username="stranger")
    service = ServiceFactory(owner=UserFactory(username="somebody-else"))
    with client.session_transaction() as session:
        session["_user_id"] = str(stranger.id)
        session["_fresh"] = True

    response = client.get(f"/dashboard/service/{service.uuid}/")

    assert response.status_code == 403


def test_admin_index_requires_staff(client):
    assert client.get("/admin/").status_code == 302
