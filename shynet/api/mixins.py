from http import HTTPStatus

from flask import jsonify, request
from sqlalchemy import select

from core.models import AnonymousUser, User
from shynet.extensions import db


class ApiTokenRequiredMixin:
    def _get_user_by_token(self, request):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Token "):
            return AnonymousUser()

        token = token.split(" ")[1]
        user: User = db.session.scalar(select(User).where(User.api_token == token))
        return user or AnonymousUser()

    def dispatch_request(self, **kwargs):
        self.user = self._get_user_by_token(request)
        return (
            super().dispatch_request(**kwargs)
            if self.user.is_authenticated
            else (jsonify({}), HTTPStatus.FORBIDDEN)
        )
