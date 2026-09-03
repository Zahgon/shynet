from http import HTTPStatus

from api.mixins import ApiTokenRequiredMixin
from core.factories import UserFactory
from core.models import _default_api_token, Service
from shynet.views import View


class DummyView(ApiTokenRequiredMixin, View):
    model = Service
    template_name = "dashboard/pages/service.html"


class TestApiTokenRequiredMixin:
    def test_get_user_by_token_without_authorization_token(self, app):
        """
        GIVEN: A request without Authorization header
        WHEN: get_user_by_token is called
        THEN: It should return AnonymousUser
        """
        with app.test_request_context("/fake-path"):
            from flask import request

            user = DummyView()._get_user_by_token(request)

        assert user.is_anonymous is True

    def test_get_user_by_token_with_invalid_authorization_token(self, app):
        """
        GIVEN: A request with invalid Authorization header
        WHEN: get_user_by_token is called
        THEN: It should return AnonymousUser
        """
        with app.test_request_context(
            "/fake-path", headers={"Authorization": "Bearer invalid-token"}
        ):
            from flask import request

            user = DummyView()._get_user_by_token(request)

        assert user.is_anonymous is True

    def test_get_user_by_token_with_invalid_token(self, app):
        """
        GIVEN: A request with invalid token
        WHEN: get_user_by_token is called
        THEN: It should return AnonymousUser
        """
        with app.test_request_context(
            "/fake-path", headers={"Authorization": f"Token {_default_api_token()}"}
        ):
            from flask import request

            user = DummyView()._get_user_by_token(request)

        assert user.is_anonymous is True

    def test_get_user_by_token_with_valid_token(self, app):
        """
        GIVEN: A request with valid token
        WHEN: get_user_by_token is called
        THEN: It should return the user
        """
        expected = UserFactory()
        with app.test_request_context(
            "/fake-path", headers={"Authorization": f"Token {expected.api_token}"}
        ):
            from flask import request

            user = DummyView()._get_user_by_token(request)

        assert user == expected

    def test_dispatch_with_unauthenticated_user(self, app):
        """
        GIVEN: A request with unauthenticated user
        WHEN: dispatch is called
        THEN: It should return 403
        """
        with app.test_request_context(
            "/fake-path", headers={"Authorization": f"Token {_default_api_token()}"}
        ):
            _body, status = DummyView().dispatch_request()

        assert status == HTTPStatus.FORBIDDEN
