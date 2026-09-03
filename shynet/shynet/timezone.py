"""Timezone helpers.

Shynet stores every timestamp in UTC and renders it in `settings.TIME_ZONE`.
These helpers replace the framework timezone utilities the project used to rely
on, keeping the exact same names and semantics.
"""

from datetime import date, datetime, time, timedelta, timezone as _timezone

try:  # Python 3.9+
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo

utc = _timezone.utc

__all__ = [
    "date",
    "datetime",
    "time",
    "timedelta",
    "utc",
    "now",
    "localdate",
    "localtime",
    "get_current_timezone",
    "make_aware",
    "is_aware",
    "is_naive",
]


def get_current_timezone():
    from . import settings

    return ZoneInfo(settings.TIME_ZONE)


def now():
    """An aware `datetime` in UTC (`USE_TZ` is always on for Shynet)."""
    return datetime.now(tz=utc)


def is_aware(value):
    return value.utcoffset() is not None


def is_naive(value):
    return value.utcoffset() is None


def make_aware(value, tz=None):
    if tz is None:
        tz = get_current_timezone()
    if is_aware(value):
        raise ValueError("make_aware expects a naive datetime, got %s" % value)
    return value.replace(tzinfo=tz)


def localtime(value=None, tz=None):
    if value is None:
        value = now()
    if tz is None:
        tz = get_current_timezone()
    if is_naive(value):
        value = value.replace(tzinfo=utc)
    return value.astimezone(tz)


def localdate(value=None, tz=None):
    return localtime(value, tz).date()
