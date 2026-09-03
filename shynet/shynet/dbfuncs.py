"""Date truncation across database backends.

PostgreSQL truncates with `date_trunc`; SQLite has no timezone support, so the
equivalent functions are registered on every connection (the same trick the
previous ORM used) and called by name.
"""

from datetime import datetime

from sqlalchemy import Date, cast, func
from sqlalchemy.engine import Engine
from sqlalchemy import event

from . import settings, timezone


def _parse(value):
    if isinstance(value, str):
        value = value.replace("T", " ")
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unable to parse truncated datetime {value!r}")
    return value


def _sqlite_datetime_trunc(kind, value, tzname):
    if value is None:
        return None
    parsed = _parse(value).replace(tzinfo=timezone.utc)
    local = parsed.astimezone(timezone.ZoneInfo(tzname))
    if kind == "hour":
        local = local.replace(minute=0, second=0, microsecond=0)
        return local.strftime("%Y-%m-%d %H:%M:%S")
    if kind == "date":
        return local.strftime("%Y-%m-%d")
    raise ValueError(f"Unsupported truncation {kind!r}")


@event.listens_for(Engine, "connect")
def _configure_sqlite_connection(dbapi_connection, connection_record):
    """Register the truncation helpers and enable foreign keys on SQLite."""
    if not hasattr(dbapi_connection, "create_function"):
        return
    try:
        dbapi_connection.create_function(
            "shynet_datetime_trunc", 3, _sqlite_datetime_trunc
        )
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:  # pragma: no cover - not a SQLite connection
        pass


def _dialect():
    from .extensions import db

    return db.engine.dialect.name


def trunc_hour(column):
    """Truncate `column` to the hour, in the active timezone."""
    tzname = settings.TIME_ZONE
    if _dialect() == "postgresql":
        return func.date_trunc("hour", func.timezone(tzname, column))
    return func.shynet_datetime_trunc("hour", column, tzname)


def trunc_date(column):
    """Truncate `column` to the date, in the active timezone."""
    tzname = settings.TIME_ZONE
    if _dialect() == "postgresql":
        return cast(func.timezone(tzname, column), Date)
    return func.shynet_datetime_trunc("date", column, tzname)


def as_local_hour(value):
    """Normalise a truncated-hour result into an aware datetime."""
    if value is None:
        return None
    value = _parse(value)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.get_current_timezone())
    return value


def as_date(value):
    """Normalise a truncated-date result into a `datetime.date`."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return _parse(value).date()
    return value
