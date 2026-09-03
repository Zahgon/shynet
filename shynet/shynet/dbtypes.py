"""Portable column types.

`GUID` and `DateTimeUTC` reproduce the storage behaviour Shynet's schema relied
on: UUIDs use PostgreSQL's native type and fall back to 32-character hex
elsewhere, and datetimes are always normalised to UTC on the way in and returned
as aware UTC values on the way out.
"""

import uuid as uuid_module
from datetime import timezone as _timezone

from sqlalchemy import CHAR, BigInteger, DateTime, Integer, String, TypeDecorator
from sqlalchemy.dialects.postgresql import INET as PG_INET
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class GUID(TypeDecorator):
    """Platform-independent UUID column."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid_module.UUID):
            value = uuid_module.UUID(str(value))
        if dialect.name == "postgresql":
            return str(value)
        return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid_module.UUID):
            return value
        return uuid_module.UUID(str(value))


class DateTimeUTC(TypeDecorator):
    """A timezone-aware datetime that is always stored and returned in UTC."""

    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(DateTime(timezone=True))
        return dialect.type_descriptor(DateTime())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=_timezone.utc)
        value = value.astimezone(_timezone.utc)
        if dialect.name == "postgresql":
            return value
        return value.replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=_timezone.utc)
        return value.astimezone(_timezone.utc)


class IPAddress(TypeDecorator):
    """An IPv4/IPv6 address: PostgreSQL's native `inet`, text elsewhere."""

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_INET())
        return dialect.type_descriptor(String(39))

    def process_bind_param(self, value, dialect):
        return None if value is None else str(value)

    def process_result_value(self, value, dialect):
        return None if value is None else str(value)


def big_integer():
    """A 64-bit integer that stays INTEGER on SQLite, where only INTEGER
    primary keys auto-increment."""
    return BigInteger().with_variant(Integer, "sqlite")
