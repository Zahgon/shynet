"""Date formatting.

`format_date` implements the format specifiers Shynet's templates pass to the
`date` filter, together with the named formats (`DATE_FORMAT`,
`DATETIME_FORMAT`, ...). Aware values are rendered in the active timezone.
"""

import calendar
import datetime
import re

from . import timezone

MONTHS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}
MONTHS_3 = {i: MONTHS[i][:3] for i in MONTHS}
MONTHS_AP = {
    1: "Jan.",
    2: "Feb.",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "Aug.",
    9: "Sept.",
    10: "Oct.",
    11: "Nov.",
    12: "Dec.",
}
WEEKDAYS = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}
WEEKDAYS_ABBR = {i: WEEKDAYS[i][:3] for i in WEEKDAYS}

NAMED_FORMATS = {
    "DATE_FORMAT": "N j, Y",
    "DATETIME_FORMAT": "N j, Y, P",
    "SHORT_DATE_FORMAT": "m/d/Y",
    "SHORT_DATETIME_FORMAT": "m/d/Y P",
    "TIME_FORMAT": "P",
    "YEAR_MONTH_FORMAT": "F Y",
    "MONTH_DAY_FORMAT": "F j",
}

# Locale-specific overrides for the named formats above, for the languages
# Shynet ships translations for.
LOCALE_FORMATS = {
    "de": {
        "DATE_FORMAT": "j. F Y",
        "DATETIME_FORMAT": "j. F Y H:i",
        "SHORT_DATE_FORMAT": "d.m.Y",
        "SHORT_DATETIME_FORMAT": "d.m.Y H:i",
        "TIME_FORMAT": "H:i",
        "YEAR_MONTH_FORMAT": "F Y",
        "MONTH_DAY_FORMAT": "j. F",
    },
    "zh": {
        "DATE_FORMAT": "Y年n月j日",
        "DATETIME_FORMAT": "Y年n月j日 H:i",
        "SHORT_DATE_FORMAT": "Y年n月j日",
        "SHORT_DATETIME_FORMAT": "Y年n月j日 H:i",
        "TIME_FORMAT": "H:i",
        "YEAR_MONTH_FORMAT": "Y年n月",
        "MONTH_DAY_FORMAT": "m月j日",
    },
}


def _active_locale():
    """The active locale, or None outside a request (or when it is English)."""
    from . import settings

    if not settings.USE_L10N:
        return None
    try:
        from flask_babel import get_locale

        locale = get_locale()
    except Exception:
        locale = None
    if locale is None:
        language = settings.LANGUAGE_CODE.replace("-", "_")
        try:
            from babel import Locale

            locale = Locale.parse(language)
        except Exception:
            return None
    return None if locale.language == "en" else locale


def _named_format(name, locale):
    if locale is not None:
        overrides = LOCALE_FORMATS.get(locale.language)
        if overrides and name in overrides:
            return overrides[name]
    return NAMED_FORMATS[name]


def _localized_names(locale):
    """Month and weekday names for `locale`, or None to use the English tables."""
    if locale is None:
        return None
    try:
        return {
            "months_wide": locale.months["format"]["wide"],
            "months_abbr": locale.months["format"]["abbreviated"],
            "days_wide": locale.days["format"]["wide"],
            "days_abbr": locale.days["format"]["abbreviated"],
        }
    except Exception:
        return None

_ESCAPE = re.compile(r"\\(.)")


def _ordinal(day):
    if 11 <= day <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")


def _time_ap(value):
    """The `P` specifier: `4 p.m.`, `4:30 p.m.`, `midnight`, `noon`."""
    if value.minute == 0 and value.hour == 0:
        return "midnight"
    if value.minute == 0 and value.hour == 12:
        return "noon"
    hour = value.hour % 12 or 12
    minute = "" if value.minute == 0 else f":{value.minute:02d}"
    meridian = "a.m." if value.hour < 12 else "p.m."
    return f"{hour}{minute} {meridian}"


def format_date(value, format_string="DATE_FORMAT"):
    if value in (None, ""):
        return ""
    locale = _active_locale()
    if format_string in NAMED_FORMATS:
        format_string = _named_format(format_string, locale)
    names = _localized_names(locale)

    if isinstance(value, datetime.datetime):
        if value.tzinfo is not None:
            value = timezone.localtime(value)
    elif isinstance(value, datetime.date):
        value = datetime.datetime(value.year, value.month, value.day)
    elif isinstance(value, datetime.time):
        value = datetime.datetime(1900, 1, 1, value.hour, value.minute, value.second)
    else:
        return ""

    output = []
    escaped = False
    for char in format_string:
        if escaped:
            output.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        handler = _SPECIFIERS.get(char)
        if handler is None:
            output.append(char)
        elif names is not None and char in _NAME_SPECIFIERS:
            output.append(_NAME_SPECIFIERS[char](value, names))
        else:
            output.append(handler(value))
    return "".join(output)


# The specifiers that render a month or weekday name, which Babel localises.
_NAME_SPECIFIERS = {
    "M": lambda v, n: n["months_abbr"][v.month],
    "b": lambda v, n: n["months_abbr"][v.month].lower(),
    "E": lambda v, n: n["months_wide"][v.month],
    "F": lambda v, n: n["months_wide"][v.month],
    "N": lambda v, n: n["months_abbr"][v.month],
    "D": lambda v, n: n["days_abbr"][v.weekday()],
    "l": lambda v, n: n["days_wide"][v.weekday()],
}


def _utcoffset_seconds(value):
    offset = value.utcoffset()
    return 0 if offset is None else int(offset.total_seconds())


_SPECIFIERS = {
    # Day
    "d": lambda v: f"{v.day:02d}",
    "j": lambda v: str(v.day),
    "D": lambda v: WEEKDAYS_ABBR[v.weekday()],
    "l": lambda v: WEEKDAYS[v.weekday()],
    "S": lambda v: _ordinal(v.day),
    "w": lambda v: str((v.weekday() + 1) % 7),
    "z": lambda v: str(v.timetuple().tm_yday),
    # Week
    "W": lambda v: str(v.isocalendar()[1]),
    # Month
    "m": lambda v: f"{v.month:02d}",
    "n": lambda v: str(v.month),
    "M": lambda v: MONTHS_3[v.month],
    "b": lambda v: MONTHS_3[v.month].lower(),
    "E": lambda v: MONTHS[v.month],
    "F": lambda v: MONTHS[v.month],
    "N": lambda v: MONTHS_AP[v.month],
    "t": lambda v: str(calendar.monthrange(v.year, v.month)[1]),
    # Year
    "y": lambda v: f"{v.year % 100:02d}",
    "Y": lambda v: f"{v.year:04d}",
    "L": lambda v: str(calendar.isleap(v.year)),
    "o": lambda v: str(v.isocalendar()[0]),
    # Time
    "g": lambda v: str(v.hour % 12 or 12),
    "G": lambda v: str(v.hour),
    "h": lambda v: f"{(v.hour % 12 or 12):02d}",
    "H": lambda v: f"{v.hour:02d}",
    "i": lambda v: f"{v.minute:02d}",
    "s": lambda v: f"{v.second:02d}",
    "u": lambda v: f"{v.microsecond:06d}",
    "a": lambda v: "a.m." if v.hour < 12 else "p.m.",
    "A": lambda v: "AM" if v.hour < 12 else "PM",
    "f": lambda v: str(v.hour % 12 or 12)
    + ("" if v.minute == 0 else f":{v.minute:02d}"),
    "P": _time_ap,
    # Timezone
    "e": lambda v: v.tzname() or "",
    "T": lambda v: v.tzname() or "",
    "O": lambda v: "{}{:02d}{:02d}".format(
        "-" if _utcoffset_seconds(v) < 0 else "+",
        abs(_utcoffset_seconds(v)) // 3600,
        (abs(_utcoffset_seconds(v)) // 60) % 60,
    ),
    "Z": lambda v: str(_utcoffset_seconds(v)),
    "U": lambda v: str(int(v.timestamp())),
    "c": lambda v: v.isoformat(),
    "r": lambda v: format_date(v, "D, j M Y H:i:s O"),
}
