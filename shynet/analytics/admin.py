from core.admin import ShynetModelView
from shynet.extensions import db

from .models import Hit, Session


class HitInline:
    """The inline used to list a session's hits on the session detail page."""

    form_columns = (
        "initial",
        "start_time",
        "last_seen",
        "heartbeats",
        "tracker",
        "location",
        "referrer",
        "load_time",
    )


class SessionAdmin(ShynetModelView):
    column_list = (
        "uuid",
        "service",
        "start_time",
        "last_seen",
        "identifier",
        "ip",
        "asn",
        "country",
    )
    column_searchable_list = (
        "ip",
        "user_agent",
        "device",
        "device_type",
        "identifier",
        "asn",
        "time_zone",
    )
    column_filters = ("device_type",)
    inline_models = [(Hit, dict(form_columns=("id",) + HitInline.form_columns))]


class HitAdmin(ShynetModelView):
    column_list = (
        "session",
        "initial",
        "start_time",
        "heartbeats",
        "tracker",
        "load_time",
        "location",
    )
    column_searchable_list = ("tracker", "location", "referrer")
    column_filters = ("initial", "tracker")


def register_admin(admin):
    admin.add_view(
        SessionAdmin(Session, db.session, name="Sessions", category="Analytics")
    )
    admin.add_view(HitAdmin(Hit, db.session, name="Hits", category="Analytics"))
