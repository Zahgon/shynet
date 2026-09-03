from flask import Blueprint

from . import views

dashboard = Blueprint("dashboard", __name__, template_folder="templates")

dashboard.add_url_rule(
    "/", view_func=views.DashboardView.as_view("dashboard"), methods=["GET"]
)
dashboard.add_url_rule(
    "/service/new/",
    view_func=views.ServiceCreateView.as_view("service_create"),
    methods=["GET", "POST"],
)
dashboard.add_url_rule(
    "/service/<pk>/", view_func=views.ServiceView.as_view("service"), methods=["GET"]
)
dashboard.add_url_rule(
    "/service/<pk>/manage/",
    view_func=views.ServiceUpdateView.as_view("service_update"),
    methods=["GET", "POST"],
)
dashboard.add_url_rule(
    "/service/<pk>/delete/",
    view_func=views.ServiceDeleteView.as_view("service_delete"),
    methods=["GET", "POST"],
)
dashboard.add_url_rule(
    "/service/<pk>/sessions/",
    view_func=views.ServiceSessionsListView.as_view("service_session_list"),
    methods=["GET"],
)
dashboard.add_url_rule(
    "/service/<pk>/sessions/<session_pk>/",
    view_func=views.ServiceSessionView.as_view("service_session"),
    methods=["GET"],
)
dashboard.add_url_rule(
    "/service/<pk>/locations/",
    view_func=views.ServiceLocationsListView.as_view("service_location_list"),
    methods=["GET"],
)
dashboard.add_url_rule(
    "/api-token-refresh/",
    view_func=views.RefreshApiTokenView.as_view("api_token_refresh"),
    methods=["POST"],
)
