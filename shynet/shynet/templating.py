"""Jinja environment setup.

Registers every filter and global the templates use — the ported template tags
from `a17t`, `dashboard` and `accounts`, plus the general-purpose filters — and
installs the context processors that make `user`, `messages` and the settings
available everywhere.
"""

from flask import get_flashed_messages
from flask_babel import get_locale
from flask_login import current_user
from markupsafe import Markup

from . import settings, templatefilters
from .messages import get_tags
from .staticfiles import static


class Message:
    """A flashed message, exposing `.tags` the way the templates expect."""

    def __init__(self, level, message):
        self.level = level
        self.message = message

    @property
    def tags(self):
        return get_tags(self.level)

    def __str__(self):
        return str(self.message)

    def __html__(self):
        return str(self.message)


def get_messages():
    return [
        Message(level, message)
        for level, message in get_flashed_messages(with_categories=True)
    ]


def csrf_input():
    """The hidden CSRF field, i.e. the replacement for `{% csrf_token %}`."""
    from flask_wtf.csrf import generate_csrf

    return Markup(
        f'<input type="hidden" name="csrf_token" value="{generate_csrf()}">'
    )


def init_app(app):
    from a17t.templatetags import a17t_tags, pagination as pagination_tags
    from accounts.adapter import user_display
    from dashboard.templatetags import helpers
    from shynet import rules

    env = app.jinja_env
    env.policies["ext.i18n.trimmed"] = True
    env.trim_blocks = settings.TEMPLATE_TRIM_BLOCKS
    env.auto_reload = settings.TEMPLATE_AUTO_RELOAD

    # General-purpose filters
    env.filters.update(
        {
            "default": templatefilters.default,
            "default_if_none": templatefilters.default_if_none,
            "intcomma": templatefilters.intcomma,
            "floatformat": templatefilters.floatformat,
            "truncatechars": templatefilters.truncatechars,
            "capfirst": templatefilters.capfirst,
            "urlize": templatefilters.urlize,
            "date": templatefilters.date,
            "time": templatefilters.time,
            "dictsort": templatefilters.dictsort,
            "dictsortreversed": templatefilters.dictsortreversed,
            "force_escape": templatefilters.force_escape,
        }
    )

    # a17t form rendering
    env.filters.update(
        {
            "a17t": a17t_tags.a17t,
            "a17t_inline": a17t_tags.a17t_inline,
            "widget_type": a17t_tags.widget_type,
            "is_select": a17t_tags.is_select,
            "is_multiple_select": a17t_tags.is_multiple_select,
            "is_textarea": a17t_tags.is_textarea,
            "is_input": a17t_tags.is_input,
            "is_checkbox": a17t_tags.is_checkbox,
            "is_multiple_checkbox": a17t_tags.is_multiple_checkbox,
            "is_radio": a17t_tags.is_radio,
            "is_file": a17t_tags.is_file,
            "is_hidden": a17t_tags.is_hidden,
            "add_class": a17t_tags.add_class,
        }
    )
    env.globals.update(
        {
            "hidden_fields": a17t_tags.hidden_fields,
            "visible_fields": a17t_tags.visible_fields,
            "non_field_errors": a17t_tags.non_field_errors,
            "pagination": pagination_tags.pagination,
        }
    )

    # Dashboard helpers
    env.filters.update(
        {
            "naturaldelta": helpers.naturaldelta,
            "flag_class": helpers.flag_class,
            "country_name": helpers.country_name,
            "datamap_id": helpers.datamap_id,
            "startswith": helpers.startswith,
            "iconify": helpers.iconify,
            "urldisplay": helpers.urldisplay,
            "location_url": helpers.location_url,
            "percent": helpers.percent,
        }
    )
    env.globals.update(
        {
            "relative_stat_tone": helpers.relative_stat_tone,
            "percent_change_display": helpers.percent_change_display,
            "sidebar_footer": helpers.sidebar_footer,
            "compare": helpers.compare,
            "contextual_url": helpers.contextual_url,
            "bar_width": helpers.bar_width,
        }
    )

    # Framework-level globals
    env.globals.update(
        {
            "static": static,
            "csrf_token_input": csrf_input,
            "has_perm": rules.has_perm,
            "get_locale": get_locale,
            "user_display": user_display,
            "settings": settings,
        }
    )

    @app.context_processor
    def _inject_context():
        return {
            "user": current_user,
            "messages": get_messages(),
            "LANGUAGE_CODE": str(get_locale()),
        }
