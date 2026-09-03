"""General-purpose template filters.

The built-in filters Shynet's templates rely on (`intcomma`, `floatformat`,
`urlize`, `date`, ...), reimplemented so the templates render identically.
"""

import re

from markupsafe import Markup, escape

from .dateformat import format_date


def default(value, arg=""):
    """Use `arg` when `value` is falsy."""
    return value if value else arg


def default_if_none(value, arg=""):
    return arg if value is None else value


def intcomma(value):
    """Group a number's integer part with commas: 1234567 -> 1,234,567."""
    if value is None or value == "":
        return ""
    try:
        if isinstance(value, str):
            number = float(value) if "." in value else int(value)
        else:
            number = value
    except (TypeError, ValueError):
        return value
    if isinstance(number, float):
        integral, _, fractional = f"{number}".partition(".")
        grouped = "{:,}".format(int(integral))
        return f"{grouped}.{fractional}" if fractional else grouped
    return "{:,}".format(number)


def floatformat(value, arg=-1):
    """Round to `arg` decimals; a negative `arg` drops trailing zeroes."""
    if value is None or value == "":
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    try:
        places = int(arg)
    except (TypeError, ValueError):
        return str(value)
    if places < 0:
        if number == int(number):
            return f"{number:.0f}"
        return f"{number:.{abs(places)}f}"
    return f"{number:.{places}f}"


def truncatechars(value, arg):
    if value is None:
        return ""
    value = str(value)
    try:
        length = int(arg)
    except (TypeError, ValueError):
        return value
    if len(value) <= length:
        return value
    if length <= 1:
        return "…"
    return value[: length - 1] + "…"


def capfirst(value):
    if not value:
        return value
    value = str(value)
    return value[0].upper() + value[1:]


_URL_RE = re.compile(r"(https?://[^\s<>\"']+|www\.[^\s<>\"']+)")


def urlize(value):
    """Turn bare URLs in `value` into links."""
    if value is None:
        return ""
    text = str(value)

    def replace(match):
        url = match.group(0)
        href = url if url.startswith("http") else "http://" + url
        return f'<a href="{escape(href)}" rel="nofollow">{escape(url)}</a>'

    return Markup(_URL_RE.sub(replace, escape(text)))


def date(value, arg="DATE_FORMAT"):
    return format_date(value, arg)


def time(value, arg="TIME_FORMAT"):
    return format_date(value, arg)


def _resolve(item, path):
    for part in path.split("."):
        try:
            item = item[part]
        except (TypeError, KeyError, IndexError, AttributeError):
            item = getattr(item, part, None)
        if item is None:
            return None
    return item


def dictsort(value, arg):
    try:
        return sorted(value, key=lambda item: (_resolve(item, arg) is None, _resolve(item, arg)))
    except TypeError:
        return ""


def dictsortreversed(value, arg):
    try:
        return sorted(
            value,
            key=lambda item: (_resolve(item, arg) is None, _resolve(item, arg)),
            reverse=True,
        )
    except TypeError:
        return ""


def force_escape(value):
    """Escape `value` even when it is already marked as safe HTML.

    `{% filter force_escape %}` blocks display markup as literal text, so the
    block's rendered output has to be escaped rather than passed through.
    """
    return escape(str(value))
