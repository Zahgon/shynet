from flask import Blueprint, redirect, url_for

from . import views

core = Blueprint("core", __name__, template_folder="templates")


@core.route("/")
def index():
    return redirect(url_for("dashboard.dashboard"))
