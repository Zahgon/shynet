"""Flash message levels and helpers.

Flask's `flash()` takes a free-form category; these constants give Shynet the
same set of levels the framework's message framework used to provide, and
`shynet.settings.MESSAGE_TAGS` maps them onto a17t CSS classes.
"""

from flask import flash as _flash

DEBUG = "debug"
INFO = "info"
SUCCESS = "success"
WARNING = "warning"
ERROR = "error"

DEFAULT_LEVELS = {
    "DEBUG": DEBUG,
    "INFO": INFO,
    "SUCCESS": SUCCESS,
    "WARNING": WARNING,
    "ERROR": ERROR,
}


def add_message(level, message):
    _flash(message, level)


def debug(message):
    add_message(DEBUG, message)


def info(message):
    add_message(INFO, message)


def success(message):
    add_message(SUCCESS, message)


def warning(message):
    add_message(WARNING, message)


def error(message):
    add_message(ERROR, message)


def get_tags(level):
    from . import settings

    return settings.MESSAGE_TAGS.get(level, "")
