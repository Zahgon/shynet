"""JSON encoding.

The API previously serialised responses with an encoder that understood
`datetime`, `date`, `time`, `timedelta`, `Decimal` and `UUID`; this provider
keeps that behaviour (durations are rendered as ISO 8601).
"""

import datetime
import decimal
import uuid

from flask.json.provider import DefaultJSONProvider


def duration_iso_string(duration):
    if duration < datetime.timedelta(0):
        sign = "-"
        duration *= -1
    else:
        sign = ""
    days = duration.days
    seconds = duration.seconds
    microseconds = duration.microseconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    ms = ".{:06d}".format(microseconds) if microseconds else ""
    return "{}P{}DT{:02d}H{:02d}M{:02d}{}S".format(
        sign, days, hours, minutes, seconds, ms
    )


def default(obj):
    if isinstance(obj, datetime.datetime):
        representation = obj.isoformat()
        if representation.endswith("+00:00"):
            representation = representation[:-6] + "Z"
        return representation
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    if isinstance(obj, datetime.time):
        return obj.isoformat()
    if isinstance(obj, datetime.timedelta):
        return duration_iso_string(obj)
    if isinstance(obj, (decimal.Decimal, uuid.UUID)):
        return str(obj)
    return DefaultJSONProvider.default(obj)


class ShynetJSONProvider(DefaultJSONProvider):
    default = staticmethod(default)
    sort_keys = False
