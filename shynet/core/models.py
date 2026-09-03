import ipaddress
import re
import uuid

from secrets import token_urlsafe

from flask import url_for
from flask_babel import lazy_gettext as _
from flask_login import UserMixin
from sqlalchemy import event, func, select

from shynet import settings, timezone
from shynet.dbfuncs import as_date, as_local_hour, trunc_date, trunc_hour
from shynet.dbtypes import DateTimeUTC, GUID, big_integer
from shynet.exceptions import NotSupportedError, ValidationError
from shynet.extensions import db

from . import hashers

# How long a session a needs to go without an update to no longer be considered 'active' (i.e., currently online)
ACTIVE_USER_TIMEDELTA = timezone.timedelta(
    milliseconds=settings.SCRIPT_HEARTBEAT_FREQUENCY * 2
)
RESULTS_LIMIT = 300


def _default_uuid():
    return str(uuid.uuid4())


def _validate_network_list(networks: str):
    try:
        _parse_network_list(networks)
    except ValueError as e:
        raise ValidationError(str(e))


def _validate_regex(regex: str):
    try:
        re.compile(regex)
    except re.error:
        raise ValidationError(f"'{regex}' is not valid RegEx")


def _parse_network_list(networks: str):
    if len(networks.strip()) == 0:
        return []
    return [ipaddress.ip_network(network.strip()) for network in networks.split(",")]


def _default_api_token():
    return token_urlsafe(32)


service_collaborators = db.Table(
    "core_service_collaborators",
    db.Column("id", big_integer(), primary_key=True, autoincrement=True),
    db.Column(
        "service_id",
        GUID(),
        db.ForeignKey("core_service.uuid", ondelete="CASCADE"),
        nullable=False,
    ),
    db.Column(
        "user_id",
        big_integer(),
        db.ForeignKey("core_user.id", ondelete="CASCADE"),
        nullable=False,
    ),
    db.UniqueConstraint("service_id", "user_id", name="core_service_collaborators_uniq"),
)


# The current site is read on every request, including the tracking endpoints,
# so it is cached in-process rather than queried each time.
SITE_CACHE = {}


class Site(db.Model):
    """The deployment's own identity (its domain and whitelabel name)."""

    __tablename__ = "core_site"

    id = db.Column(big_integer(), primary_key=True, autoincrement=True)
    domain = db.Column(db.String(100), nullable=False, unique=True)
    name = db.Column(db.String(50), nullable=False)

    def __str__(self):
        return self.domain

    @property
    def pk(self):
        return self.id

    @classmethod
    def get_current(cls):
        site_id = settings.SITE_ID
        if site_id not in SITE_CACHE:
            site = db.session.get(cls, site_id)
            if site is None:
                return None
            SITE_CACHE[site_id] = site
        return SITE_CACHE[site_id]

    @classmethod
    def clear_cache(cls):
        SITE_CACHE.clear()


@event.listens_for(db.session, "after_commit")
def _clear_site_cache(session):
    """Drop the cached site whenever one is written, as the signals did."""
    if any(isinstance(obj, Site) for obj in session.identity_map.values()):
        Site.clear_cache()


class User(UserMixin, db.Model):
    __tablename__ = "core_user"

    id = db.Column(big_integer(), primary_key=True, autoincrement=True)
    password = db.Column(db.String(128), nullable=False)
    last_login = db.Column(DateTimeUTC(), nullable=True)
    is_superuser = db.Column(db.Boolean, nullable=False, default=False)
    first_name = db.Column(db.String(150), nullable=False, default="")
    last_name = db.Column(db.String(150), nullable=False, default="")
    is_staff = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    date_joined = db.Column(DateTimeUTC(), nullable=False, default=timezone.now)

    username = db.Column(db.Text, nullable=False, unique=True, default=_default_uuid)
    email = db.Column(db.String(254), nullable=False, unique=True)
    api_token = db.Column(db.Text, unique=True, default=_default_api_token)

    def __str__(self):
        return self.email

    @property
    def pk(self):
        return self.id

    # Authentication -------------------------------------------------------

    def get_id(self):
        return str(self.id)

    def set_password(self, raw_password):
        self.password = hashers.make_password(raw_password)

    def check_password(self, raw_password):
        return hashers.check_password(raw_password, self.password)

    def set_unusable_password(self):
        self.password = hashers.make_unusable_password()

    def has_usable_password(self):
        return hashers.is_password_usable(self.password)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_anonymous(self):
        return False

    # Managers -------------------------------------------------------------

    @classmethod
    def create_user(cls, username, email, password=None, **extra_fields):
        user = cls(username=username, email=email, **extra_fields)
        if password is None:
            user.set_unusable_password()
        else:
            user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def create_superuser(cls, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return cls.create_user(username, email, password, **extra_fields)


class AnonymousUser:
    """The `current_user` stand-in for unauthenticated requests."""

    id = None
    pk = None
    email = ""
    username = ""
    is_staff = False
    is_superuser = False
    is_active = False

    @property
    def is_authenticated(self):
        return False

    @property
    def is_anonymous(self):
        return True

    def get_id(self):
        return None

    def __str__(self):
        return "AnonymousUser"

    def __eq__(self, other):
        return isinstance(other, AnonymousUser)

    def __hash__(self):
        return hash("AnonymousUser")


class Service(db.Model):
    __tablename__ = "core_service"

    ACTIVE = "AC"
    ARCHIVED = "AR"
    SERVICE_STATUSES = [(ACTIVE, _("Active")), (ARCHIVED, _("Archived"))]

    uuid = db.Column(GUID(), primary_key=True, default=_default_uuid)
    name = db.Column(db.Text, nullable=False, info={"verbose_name": _("Name")})
    owner_id = db.Column(
        big_integer(),
        db.ForeignKey("core_user.id", ondelete="CASCADE"),
        nullable=False,
        info={"verbose_name": _("Owner")},
    )
    created = db.Column(
        DateTimeUTC(),
        nullable=False,
        default=timezone.now,
        info={"verbose_name": _("created")},
    )
    link = db.Column(
        db.String(200), nullable=False, default="", info={"verbose_name": _("link")}
    )
    origins = db.Column(
        db.Text, nullable=False, default="*", info={"verbose_name": _("origins")}
    )
    status = db.Column(
        db.String(2),
        nullable=False,
        default=ACTIVE,
        index=True,
        info={"verbose_name": _("status")},
    )
    respect_dnt = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        info={"verbose_name": _("Respect dnt")},
    )
    ignore_robots = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        info={"verbose_name": _("Ignore robots")},
    )
    collect_ips = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        info={"verbose_name": _("Collect ips")},
    )
    ignored_ips = db.Column(
        db.Text,
        nullable=False,
        default="",
        info={"verbose_name": _("Igored ips"), "validators": [_validate_network_list]},
    )
    hide_referrer_regex = db.Column(
        db.Text,
        nullable=False,
        default="",
        info={
            "verbose_name": _("Hide referrer regex"),
            "validators": [_validate_regex],
        },
    )
    script_inject = db.Column(
        db.Text,
        nullable=False,
        default="",
        info={"verbose_name": _("Script inject")},
    )

    owner = db.relationship(
        "User",
        backref=db.backref(
            "owning_services",
            lazy="dynamic",
            order_by=lambda: (Service.name, Service.uuid),
            cascade="all, delete",
            passive_deletes=True,
        ),
    )
    collaborators = db.relationship(
        "User",
        secondary=service_collaborators,
        info={"verbose_name": _("Collaborators")},
        backref=db.backref(
            "collaborating_services",
            lazy="dynamic",
            order_by=lambda: (Service.name, Service.uuid),
        ),
    )

    def __str__(self):
        return self.name

    @property
    def pk(self):
        return self.uuid

    @classmethod
    def default_order(cls):
        """The model's default ordering (`name`, then `uuid`)."""
        return (cls.name, cls.uuid)

    def validate(self):
        _validate_network_list(self.ignored_ips or "")
        _validate_regex(self.hide_referrer_regex or "")

    def get_ignored_networks(self):
        return _parse_network_list(self.ignored_ips)

    def get_ignored_referrer_regex(self):
        if len(self.hide_referrer_regex.strip()) == 0:
            return re.compile(r".^")  # matches nothing
        else:
            try:
                return re.compile(self.hide_referrer_regex)
            except re.error:
                # Regexes are validated in the form, but this is an important
                # fallback to prevent form validation and malformed source
                # data from causing all service pages to error
                return re.compile(r".^")

    def get_daily_stats(self):
        return self.get_core_stats(
            start_time=timezone.now() - timezone.timedelta(days=1)
        )

    def get_core_stats(self, start_time=None, end_time=None):
        if start_time is None:
            start_time = timezone.now() - timezone.timedelta(days=30)
        if end_time is None:
            end_time = timezone.now()

        main_data = self.get_relative_stats(start_time, end_time)
        comparison_data = self.get_relative_stats(
            start_time - (end_time - start_time), start_time
        )
        main_data["compare"] = comparison_data

        return main_data

    def get_relative_stats(self, start_time, end_time):
        from analytics.models import Hit, Session

        tz_now = timezone.now()

        currently_online = db.session.scalar(
            select(func.count())
            .select_from(Session)
            .where(
                Session.service_id == self.uuid,
                Session.last_seen > tz_now - ACTIVE_USER_TIMEDELTA,
            )
        )

        session_filters = (
            Session.service_id == self.uuid,
            Session.start_time > start_time,
            Session.start_time < end_time,
        )
        session_count = db.session.scalar(
            select(func.count()).select_from(Session).where(*session_filters)
        )

        hit_filters = (
            Hit.service_id == self.uuid,
            Hit.start_time < end_time,
            Hit.start_time > start_time,
        )
        hit_count = db.session.scalar(
            select(func.count()).select_from(Hit).where(*hit_filters)
        )

        has_hits = bool(
            db.session.scalar(
                select(func.count())
                .select_from(Hit)
                .where(Hit.service_id == self.uuid)
                .limit(1)
            )
        )

        bounce_count = db.session.scalar(
            select(func.count())
            .select_from(Session)
            .where(*session_filters, Session.is_bounce.is_(True))
        )

        locations = self._group_count(Hit.location, hit_filters, "location")

        referrer_ignore = self.get_ignored_referrer_regex()
        referrers = [
            referrer
            for referrer in self._group_count(
                Hit.referrer, hit_filters + (Hit.initial.is_(True),), "referrer"
            )
            if not referrer_ignore.match(referrer["referrer"])
        ]

        countries = self._group_count(Session.country, session_filters, "country")

        operating_systems = self._group_count(Session.os, session_filters, "os")

        browsers = self._group_count(Session.browser, session_filters, "browser")

        device_types = self._group_count(
            Session.device_type, session_filters, "device_type"
        )

        devices = self._group_count(Session.device, session_filters, "device")

        avg_load_time = db.session.scalar(
            select(func.avg(Hit.load_time)).where(*hit_filters)
        )

        avg_hits_per_session = hit_count / session_count if session_count > 0 else None

        avg_session_duration = self._get_avg_session_duration(
            session_filters, session_count
        )

        chart_data, chart_tooltip_format, chart_granularity = self._get_chart_data(
            session_filters, hit_filters, start_time, end_time, tz_now
        )

        return {
            "currently_online": currently_online,
            "session_count": session_count,
            "hit_count": hit_count,
            "has_hits": has_hits,
            "bounce_rate_pct": bounce_count * 100 / session_count
            if session_count > 0
            else None,
            "avg_session_duration": avg_session_duration,
            "avg_load_time": avg_load_time,
            "avg_hits_per_session": avg_hits_per_session,
            "locations": locations,
            "referrers": referrers,
            "countries": countries,
            "operating_systems": operating_systems,
            "browsers": browsers,
            "devices": devices,
            "device_types": device_types,
            "chart_data": chart_data,
            "chart_tooltip_format": chart_tooltip_format,
            "chart_granularity": chart_granularity,
            "online": True,
        }

    def _group_count(self, column, filters, key):
        """Count rows grouped by `column`, most frequent first."""
        count = func.count(column).label("count")
        rows = db.session.execute(
            select(column, count)
            .where(*filters)
            .group_by(column)
            .order_by(count.desc())
            .limit(RESULTS_LIMIT)
        )
        return [{key: row[0], "count": row[1]} for row in rows]

    def _get_avg_session_duration(self, session_filters, session_count):
        from analytics.models import Session

        try:
            if db.engine.dialect.name != "postgresql":
                # Only PostgreSQL can average a difference of two timestamps.
                raise NotSupportedError(
                    "This backend does not support duration expressions."
                )
            avg_session_duration = db.session.scalar(
                select(func.avg(Session.last_seen - Session.start_time)).where(
                    *session_filters
                )
            )
        except NotSupportedError:
            durations = db.session.execute(
                select(Session.start_time, Session.last_seen).where(*session_filters)
            )
            avg_session_duration = sum(
                [
                    (last_seen - start_time).total_seconds()
                    for start_time, last_seen in durations
                ]
            ) / max(session_count, 1)
        if session_count == 0:
            avg_session_duration = None

        return avg_session_duration

    def _get_chart_data(
        self, session_filters, hit_filters, start_time, end_time, tz_now
    ):
        from analytics.models import Hit, Session

        # Show hourly chart for date ranges of 3 days or less, otherwise daily chart
        if (end_time - start_time).days < 3:
            chart_tooltip_format = "MM/dd HH:mm"
            chart_granularity = "hourly"
            sessions_per_hour = self._group_by_period(
                Session, Session.uuid, session_filters, trunc_hour, as_local_hour
            )
            chart_data = {
                k["period"]: {"sessions": k["count"], "hits": 0}
                for k in sessions_per_hour
            }
            hits_per_hour = self._group_by_period(
                Hit, Hit.id, hit_filters, trunc_hour, as_local_hour
            )
            for k in hits_per_hour:
                if k["period"] not in chart_data:
                    chart_data[k["period"]] = {"hits": k["count"], "sessions": 0}
                else:
                    chart_data[k["period"]]["hits"] = k["count"]

            hours_range = range(int((end_time - start_time).total_seconds() / 3600) + 1)
            for hour_offset in hours_range:
                hour = start_time + timezone.timedelta(hours=hour_offset)
                if hour not in chart_data and hour <= tz_now:
                    chart_data[hour] = {"sessions": 0, "hits": 0}
        else:
            chart_tooltip_format = "MMM d"
            chart_granularity = "daily"
            sessions_per_day = self._group_by_period(
                Session, Session.uuid, session_filters, trunc_date, as_date
            )
            chart_data = {
                k["period"]: {"sessions": k["count"], "hits": 0}
                for k in sessions_per_day
            }
            hits_per_day = self._group_by_period(
                Hit, Hit.id, hit_filters, trunc_date, as_date
            )
            for k in hits_per_day:
                if k["period"] not in chart_data:
                    chart_data[k["period"]] = {"hits": k["count"], "sessions": 0}
                else:
                    chart_data[k["period"]]["hits"] = k["count"]

            for day_offset in range((end_time - start_time).days + 1):
                day = (start_time + timezone.timedelta(days=day_offset)).date()
                if day not in chart_data and day <= tz_now.date():
                    chart_data[day] = {"sessions": 0, "hits": 0}

        chart_data = sorted(chart_data.items(), key=lambda k: k[0])
        chart_data = {
            "sessions": [v["sessions"] for k, v in chart_data],
            "hits": [v["hits"] for k, v in chart_data],
            "labels": [str(k) for k, v in chart_data],
        }

        return chart_data, chart_tooltip_format, chart_granularity

    def _group_by_period(self, model, count_column, filters, truncate, normalize):
        period = truncate(model.start_time).label("period")
        count = func.count(count_column).label("count")
        rows = db.session.execute(
            select(period, count).where(*filters).group_by(period).order_by(period)
        )
        return [{"period": normalize(row[0]), "count": row[1]} for row in rows]

    def get_absolute_url(self):
        return url_for("dashboard.service", pk=self.pk)

