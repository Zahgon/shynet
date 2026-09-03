"""The API must serialise a duration, which PostgreSQL returns as a timedelta.

SQLite takes a different branch and returns a float, so this is asserted
directly against the conversion helper as well as through the endpoint.
"""

import json
from datetime import timedelta

from core.factories import ServiceFactory, UserFactory
from core.models import Service


def test_conversion_leaves_non_result_values_alone():
    """
    GIVEN: Stats containing a timedelta, as PostgreSQL produces
    WHEN: The querysets are converted to lists
    THEN: The timedelta should be passed through untouched
    """
    from api.views import DashboardApiView

    duration = timedelta(seconds=42)
    services_data = [
        {"stats": {"avg_session_duration": duration, "compare": {"avg_session_duration": duration}}}
    ]

    converted = DashboardApiView()._convert_querysets_to_lists(services_data)

    assert converted[0]["stats"]["avg_session_duration"] == duration
    assert converted[0]["stats"]["compare"]["avg_session_duration"] == duration


def test_dashboard_api_serialises_a_timedelta_duration(app, client, monkeypatch):
    """
    GIVEN: A backend that reports the average session duration as a timedelta
    WHEN: The dashboard API is called
    THEN: It should return 200 with the duration as an ISO 8601 interval
    """
    user = UserFactory()
    ServiceFactory(owner=user)

    monkeypatch.setattr(
        Service,
        "_get_avg_session_duration",
        lambda self, filters, count: timedelta(seconds=42, microseconds=500000),
    )

    response = client.get(
        "/api/v1/dashboard/", headers={"Authorization": f"Token {user.api_token}"}
    )

    assert response.status_code == 200
    stats = json.loads(response.data)["services"][0]["stats"]
    assert stats["avg_session_duration"] == "P0DT00H00M42.500000S"
    assert stats["compare"]["avg_session_duration"] == "P0DT00H00M42.500000S"
