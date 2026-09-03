from flask import redirect, request, url_for
from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from shynet.extensions import db

from .models import Service, Site, User


class StaffOnlyMixin:
    """Only active staff members get into the admin."""

    def is_accessible(self):
        return (
            current_user.is_authenticated
            and current_user.is_active
            and current_user.is_staff
        )

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("accounts.login", next=request.full_path.rstrip("?")))


class ShynetAdminIndexView(StaffOnlyMixin, AdminIndexView):
    """The admin landing page, which is staff-only just like the rest of it."""


class ShynetModelView(StaffOnlyMixin, ModelView):
    pass


class UserAdmin(ShynetModelView):
    column_list = ("username", "email", "first_name", "last_name", "is_staff")
    column_searchable_list = ("username", "email", "first_name", "last_name")
    column_filters = ("is_staff", "is_superuser", "is_active")
    # The password is stored as a hash and is changed through the account pages.
    form_excluded_columns = ("password", "last_login", "date_joined")
    form_columns = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "is_superuser",
        "api_token",
    )


class ServiceAdmin(ShynetModelView):
    column_list = ("name", "link", "owner", "status")
    column_filters = ("status",)
    column_searchable_list = ("name", "link")
    form_columns = (
        "name",
        "owner",
        "collaborators",
        "link",
        "origins",
        "status",
        "respect_dnt",
        "ignore_robots",
        "collect_ips",
        "ignored_ips",
        "hide_referrer_regex",
        "script_inject",
    )


class SiteAdmin(ShynetModelView):
    column_list = ("domain", "name")
    column_searchable_list = ("domain", "name")
    form_columns = ("domain", "name")


def register_admin(admin):
    admin.add_view(UserAdmin(User, db.session, name="Users", category="Core"))
    admin.add_view(ServiceAdmin(Service, db.session, name="Services", category="Core"))
    admin.add_view(SiteAdmin(Site, db.session, name="Sites", category="Core"))
