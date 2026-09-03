from flask import Blueprint

from . import views

api = Blueprint("api", __name__, template_folder="templates")

api.add_url_rule(
    "/dashboard/",
    view_func=views.DashboardApiView.as_view("services"),
    methods=["GET"],
)
