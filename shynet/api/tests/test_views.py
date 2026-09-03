import json
from http import HTTPStatus

from core.factories import UserFactory, ServiceFactory
from core.models import Service, User


class TestDashboardApiView:
    def setup(self, app):
        self.user: User = UserFactory()
        self.service_1: Service = ServiceFactory(owner=self.user)
        self.service_2: Service = ServiceFactory(owner=self.user)
        self.url = "/api/v1/dashboard/"

    def test_get_with_unauthenticated_user(self, app, client):
        """
        GIVEN: An unauthenticated user
        WHEN: The user makes a GET request to the dashboard API view
        THEN: It should return 403
        """
        self.setup(app)
        response = client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get_returns_400(self, app, client):
        """
        GIVEN: An authenticated user
        WHEN: The user makes a GET request to the dashboard API view with an invalid date format
        THEN: It should return 400
        """
        self.setup(app)
        response = client.get(
            self.url,
            query_string={"startDate": "01/01/2000"},
            headers={"Authorization": f"Token {self.user.api_token}"},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

        data = json.loads(response.data)
        assert data["error"] == "Invalid date format. Use YYYY-MM-DD."

    def test_get_with_authenticated_user(self, app, client):
        """
        GIVEN: An authenticated user
        WHEN: The user makes a GET request to the dashboard API view
        THEN: It should return 200
        """
        self.setup(app)
        response = client.get(
            self.url, headers={"Authorization": f"Token {self.user.api_token}"}
        )
        assert response.status_code == HTTPStatus.OK

        data = json.loads(response.data)
        assert len(data["services"]) == 2

    def test_get_with_service_uuid(self, app, client):
        """
        GIVEN: An authenticated user
        WHEN: The user makes a GET request to the dashboard API view with a service UUID
        THEN: It should return 200 and a single service
        """
        self.setup(app)
        response = client.get(
            self.url,
            query_string={"uuid": str(self.service_1.uuid)},
            headers={"Authorization": f"Token {self.user.api_token}"},
        )
        assert response.status_code == HTTPStatus.OK

        data = json.loads(response.data)
        assert len(data["services"]) == 1
        assert data["services"][0]["uuid"] == str(self.service_1.uuid)
        assert data["services"][0]["name"] == str(self.service_1.name)
