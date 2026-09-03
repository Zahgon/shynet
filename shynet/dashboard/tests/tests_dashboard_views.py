from core.factories import UserFactory
from shynet import settings


class TestDashboardViews:
    def tests_unauthenticated_dashboard_view(self, app, client):
        """
        GIVEN: Unauthenticated user
        WHEN: Accessing the dashboard view
        THEN: It's redirected to login page with NEXT url to dashboard
        """
        login_url = settings.LOGIN_URL
        response = client.get("/dashboard/")

        assert response.status_code == 302
        assert response.headers["Location"] == f"{login_url}?next=/dashboard/"

    def tests_authenticated_dashboard_view(self, app, client):
        """
        GIVEN: Authenticated user
        WHEN: Accessing the dashboard view
        THEN: It should respond with 200 and render the view
        """
        user = UserFactory()
        with client.session_transaction() as session:
            session["_user_id"] = str(user.id)
            session["_fresh"] = True

        response = client.get("/dashboard/")
        assert response.status_code == 200
