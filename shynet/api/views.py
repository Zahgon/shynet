from http import HTTPStatus

from flask import jsonify, request
from sqlalchemy import or_, select
from sqlalchemy.engine import Result, ScalarResult

from core.models import Service
from core.utils import is_valid_uuid
from dashboard.mixins import DateRangeMixin
from shynet.extensions import db
from shynet.views import View

from .mixins import ApiTokenRequiredMixin


class DashboardApiView(ApiTokenRequiredMixin, DateRangeMixin, View):
    def get(self, **kwargs):
        statement = (
            select(Service)
            .where(
                or_(
                    Service.owner_id == self.user.id,
                    Service.collaborators.any(id=self.user.id),
                )
            )
            .order_by(*Service.default_order())
        )

        uuid_ = request.args.get("uuid")
        if uuid_ and is_valid_uuid(uuid_):
            statement = statement.where(Service.uuid == uuid_)

        try:
            start = self.get_start_date()
            end = self.get_end_date()
        except ValueError:
            return (
                jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}),
                HTTPStatus.BAD_REQUEST,
            )

        services = db.session.execute(statement).scalars()

        service: Service
        services_data = [
            {
                "name": service.name,
                "uuid": str(service.uuid),
                "link": service.link,
                "stats": service.get_core_stats(start, end),
            }
            for service in services
        ]

        services_data = self._convert_querysets_to_lists(services_data)

        return jsonify({"services": services_data})

    def _convert_querysets_to_lists(self, services_data: list) -> list:
        """Materialise any lazy result set so it can be serialised.

        Only result sets are converted. Everything else is left alone and
        handed to the JSON encoder as-is -- notably `avg_session_duration`,
        which PostgreSQL returns as a `timedelta`.
        """
        for service_data in services_data:
            for key, value in service_data["stats"].items():
                if isinstance(value, (Result, ScalarResult)):
                    service_data["stats"][key] = list(value)
            for key, value in service_data["stats"]["compare"].items():
                if isinstance(value, (Result, ScalarResult)):
                    service_data["stats"]["compare"][key] = list(value)

        return services_data
