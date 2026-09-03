import uuid

from flask import url_for
from flask_babel import lazy_gettext as _
from sqlalchemy import Index

from shynet import timezone
from shynet.dbtypes import DateTimeUTC, GUID, IPAddress, big_integer
from shynet.extensions import db

from core.models import Service, ACTIVE_USER_TIMEDELTA


def _default_uuid():
    return str(uuid.uuid4())


class Session(db.Model):
    __tablename__ = "analytics_session"

    uuid = db.Column(GUID(), primary_key=True, default=_default_uuid)
    service_id = db.Column(
        GUID(),
        db.ForeignKey("core_service.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
        info={"verbose_name": _("Service")},
    )

    # Cross-session identification; optional, and provided by the service
    identifier = db.Column(
        db.Text,
        nullable=False,
        default="",
        index=True,
        info={"verbose_name": _("Identifier")},
    )

    # Time
    start_time = db.Column(
        DateTimeUTC(),
        nullable=False,
        default=timezone.now,
        index=True,
        info={"verbose_name": _("Start time")},
    )
    last_seen = db.Column(
        DateTimeUTC(),
        nullable=False,
        default=timezone.now,
        index=True,
        info={"verbose_name": _("Last seen")},
    )

    # Core request information
    user_agent = db.Column(
        db.Text, nullable=False, info={"verbose_name": _("User agent")}
    )
    browser = db.Column(db.Text, nullable=False, info={"verbose_name": _("Browser")})
    device = db.Column(db.Text, nullable=False, info={"verbose_name": _("Device")})
    DEVICE_TYPES = [
        ("PHONE", _("Phone")),
        ("TABLET", _("Tablet")),
        ("DESKTOP", _("Desktop")),
        ("ROBOT", _("Robot")),
        ("OTHER", _("Other")),
    ]
    device_type = db.Column(
        db.String(7),
        nullable=False,
        default="OTHER",
        info={"verbose_name": _("Device type"), "choices": DEVICE_TYPES},
    )
    os = db.Column(db.Text, nullable=False, info={"verbose_name": _("OS")})
    ip = db.Column(
        IPAddress(), nullable=True, index=True, info={"verbose_name": _("IP")}
    )

    # GeoIP data
    asn = db.Column(
        db.Text, nullable=False, default="", info={"verbose_name": _("Asn")}
    )
    country = db.Column(
        db.Text, nullable=False, default="", info={"verbose_name": _("Country")}
    )
    longitude = db.Column(db.Float, nullable=True, info={"verbose_name": _("Longitude")})
    latitude = db.Column(db.Float, nullable=True, info={"verbose_name": _("Latitude")})
    time_zone = db.Column(
        db.Text, nullable=False, default="", info={"verbose_name": _("Time zone")}
    )

    is_bounce = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
        info={"verbose_name": _("Is bounce")},
    )

    service = db.relationship(
        Service,
        backref=db.backref(
            "session_set",
            lazy="dynamic",
            order_by=lambda: Session.start_time.desc(),
            cascade="all, delete",
            passive_deletes=True,
        ),
    )

    __table_args__ = (
        Index("analytics_session_service_start_time_idx", "service_id", start_time.desc()),
        Index("analytics_session_service_last_seen_idx", "service_id", last_seen.desc()),
        Index("analytics_session_service_identifier_idx", "service_id", "identifier"),
    )

    @classmethod
    def default_order(cls):
        return (cls.start_time.desc(),)

    @property
    def pk(self):
        return self.uuid

    @property
    def is_currently_active(self):
        return timezone.now() - self.last_seen < ACTIVE_USER_TIMEDELTA

    @property
    def duration(self):
        return self.last_seen - self.start_time

    def __str__(self):
        return f"{self.identifier if self.identifier != '' else 'Anonymous'} @ {self.service.name} [{str(self.uuid)[:6]}]"

    def get_absolute_url(self):
        return url_for(
            "dashboard.service_session", pk=self.service.pk, session_pk=self.uuid
        )

    def recalculate_bounce(self):
        bounce = self.hit_set.count() == 1
        if bounce != self.is_bounce:
            self.is_bounce = bounce
            db.session.add(self)
            db.session.commit()


class Hit(db.Model):
    __tablename__ = "analytics_hit"

    id = db.Column(big_integer(), primary_key=True, autoincrement=True)
    session_id = db.Column(
        GUID(),
        db.ForeignKey("analytics_session.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
        info={"verbose_name": _("Session")},
    )
    initial = db.Column(db.Boolean, nullable=False, default=True, index=True)

    # Base request information
    start_time = db.Column(
        DateTimeUTC(), nullable=False, default=timezone.now, index=True
    )
    last_seen = db.Column(
        DateTimeUTC(), nullable=False, default=timezone.now, index=True
    )
    heartbeats = db.Column(db.Integer, nullable=False, default=0)
    TRACKERS = [("JS", "JavaScript"), ("PIXEL", "Pixel (noscript)")]
    tracker = db.Column(
        db.Text, nullable=False, info={"choices": TRACKERS}
    )  # Tracking pixel or JS

    # Advanced page information
    location = db.Column(db.Text, nullable=False, default="", index=True)
    referrer = db.Column(db.Text, nullable=False, default="", index=True)
    load_time = db.Column(db.Float, nullable=True, index=True)

    # While not necessary, we store the root service directly for performance.
    # It makes querying much easier; no need for inner joins.
    service_id = db.Column(
        GUID(),
        db.ForeignKey("core_service.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session = db.relationship(
        Session,
        backref=db.backref(
            "hit_set",
            lazy="dynamic",
            order_by=lambda: Hit.start_time.desc(),
            cascade="all, delete",
            passive_deletes=True,
        ),
    )
    service = db.relationship(
        Service,
        backref=db.backref(
            "hit_set",
            lazy="dynamic",
            order_by=lambda: Hit.start_time.desc(),
            cascade="all, delete",
            passive_deletes=True,
        ),
    )

    __table_args__ = (
        Index("analytics_hit_session_start_time_idx", "session_id", start_time.desc()),
        Index("analytics_hit_service_start_time_idx", "service_id", start_time.desc()),
        Index("analytics_hit_session_location_idx", "session_id", "location"),
        Index("analytics_hit_session_referrer_idx", "session_id", "referrer"),
    )

    @classmethod
    def default_order(cls):
        return (cls.start_time.desc(),)

    @property
    def pk(self):
        return self.id

    @property
    def duration(self):
        return self.last_seen - self.start_time

    def get_absolute_url(self):
        return url_for(
            "dashboard.service_session",
            pk=self.service.pk,
            session_pk=self.session.pk,
        )
