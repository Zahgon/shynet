"""Dashboard template helpers.

Every filter and tag the dashboard templates used, ported to plain functions;
`shynet.templating` registers them on the Jinja environment under the same
names.
"""

from datetime import timedelta
from urllib.parse import urlparse
import urllib

import pycountry
from flask import render_template, request, url_for
from markupsafe import Markup, escape

from shynet import settings, timezone


def naturaldelta(timedelta_value):
    if isinstance(timedelta_value, timezone.timedelta):
        seconds = timedelta_value.seconds
    else:
        seconds = timedelta_value
    string = ""
    if seconds // 3600 > 0:
        string += "{:02.0f}:".format(seconds // 3600)
    string += "{:02.0f}:".format((seconds % 3600) // 60)
    string += "{:02.0f}".format(seconds % 60)
    return string


def flag_class(isocode):
    if isocode:
        return "mr-1 flag-icon flag-icon-" + isocode.lower()
    else:
        return "hidden"


def country_name(isocode):
    try:
        return pycountry.countries.get(alpha_2=isocode).name
    except:
        return "Unknown"


def datamap_id(isocode):
    try:
        return pycountry.countries.get(alpha_2=isocode).alpha_3
    except:
        return "UNKNOWN"


def relative_stat_tone(
    start,
    end,
    good="UP",
    good_classes=None,
    bad_classes=None,
    neutral_classes=None,
):
    good_classes = good_classes or "~positive"
    bad_classes = bad_classes or "~critical"
    neutral_classes = neutral_classes or "~neutral"

    if start == None or end == None or start == end:
        return neutral_classes
    if good == "UP":
        return good_classes if start <= end else bad_classes
    elif good == "DOWN":
        return bad_classes if start <= end else good_classes
    else:
        return neutral_classes


def percent_change_display(start, end):
    if start == None or end == None:
        return Markup("&Delta; n/a")
    if start == end:
        direction = "&Delta; "
    else:
        direction = "&uarr; " if end > start else "&darr; "

    if start == 0 and end != 0:
        pct_change = "100%"
    elif start == 0:
        pct_change = "0%"
    else:
        change = int(round(100 * abs(end - start) / max(start, 1)))
        if change > 999:
            return "> 999%"
        else:
            pct_change = str(change) + "%"

    return Markup(direction + pct_change)


def sidebar_footer():
    return Markup(
        render_template(
            "dashboard/includes/sidebar_footer.html",
            version=settings.VERSION if settings.SHOW_SHYNET_VERSION else "",
        )
    )


def compare(
    start,
    end,
    good,
    classes="badge",
    good_classes=None,
    bad_classes=None,
    neutral_classes=None,
):
    if isinstance(start, timedelta):
        start = start.seconds

    if isinstance(end, timedelta):
        end = end.seconds

    return Markup(
        render_template(
            "dashboard/includes/stat_comparison.html",
            start=start,
            end=end,
            good=good,
            classes=classes,
            good_classes=good_classes,
            bad_classes=bad_classes,
            neutral_classes=neutral_classes,
        )
    )


def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False


def iconify(text):
    if not settings.SHOW_THIRD_PARTY_ICONS:
        return ""

    text = text.lower()
    icons = {
        "chrome": "chrome.com",
        "safari": "www.apple.com",
        "windows": "windows.com",
        "edge": "microsoft.com",
        "firefox": "firefox.com",
        "opera": "opera.com",
        "unknown": "example.com",
        "linux": "kernel.org",
        "ios": "www.apple.com",
        "mac": "www.apple.com",
        "macos": "www.apple.com",
        "mac os x": "www.apple.com",
        "android": "android.com",
        "chrome os": "chrome.com",
        "ubuntu": "ubuntu.com",
        "fedora": "getfedora.org",
        "mobile safari": "www.apple.com",
        "chrome mobile ios": "chrome.com",
        "chrome mobile": "chrome.com",
        "samsung internet": "samsung.com",
        "google": "google.com",
        "chrome mobile webview": "chrome.com",
        "firefox mobile": "firefox.com",
        "edge mobile": "microsoft.com",
        "chromium": "chromium.org",
        "duckduckgo mobile": "duckduckgo.com",
    }

    domain = None
    if text.startswith("http"):
        domain = urlparse(text).netloc
    elif text in icons:
        domain = icons[text]
    else:
        # This fallback works better than you'd think!
        domain = text + ".com"

    return Markup(
        f'<span class="icon mr-1 flex-none"><img src="https://icons.duckduckgo.com/ip3/{escape(domain)}.ico"></span>'
    )


def urldisplay(url):
    if url.startswith("http"):
        display_url = url.replace("http://", "").replace("https://", "")
        return Markup(
            f"<a href='{escape(url)}' title='{escape(url)}' rel='nofollow' class='flex items-center mr-1 truncate'>{iconify(url)}<span class='truncate'>{escape(display_url)}</span></a>"
        )
    else:
        return url


CONTEXT_PARAMS = ["startDate", "endDate"]


def contextual_url(endpoint, **kwargs):
    """Build a URL that carries the current start/end date parameters along."""
    url = url_for(endpoint, **kwargs)

    url_parts = list(urlparse(url))
    query = dict(urllib.parse.parse_qsl(url_parts[4]))

    query.update(
        {
            param: request.args.get(param)
            for param in CONTEXT_PARAMS
            if param in request.args and param not in query
        }
    )

    url_parts[4] = urllib.parse.urlencode(query)

    return urllib.parse.urlunparse(url_parts)


def location_url(session):
    return settings.LOCATION_URL.replace("$LATITUDE", str(session.latitude)).replace(
        "$LONGITUDE", str(session.longitude)
    )


def percent(value, total):
    if total == 0:
        return "N/A"

    percent = value / total

    if percent < 0.001:
        return "<0.1%"

    return f"{percent:.1%}"


def bar_width(count, max, total):
    if total == 0 or max == 0:
        return "0"

    if settings.USE_RELATIVE_MAX_IN_BAR_VISUALIZATION:
        percent = count / max
    else:
        percent = count / total

    if percent < 0.001:
        return "0"

    return f"{percent:.1%}"
