"""
Settings for Shynet.

Configuration is read from environment variables (optionally loaded from a
`.env` file). The module-level constants below are consumed both by the Flask
application factory (see `shynet.app.create_app`) and directly by application
code, which imports this module directly.
"""

import os

from dotenv import load_dotenv

# import module sys to get the type of exception
import sys
import urllib.parse as urlparse

# Messages
from . import messages

# Load environment variables
load_dotenv()

# Increment on new releases
VERSION = "0.13.1"

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production

# SECURITY WARNING: keep the secret key used in production secret!
# `DJANGO_SECRET_KEY` is still read so that deployments predating the move to
# Flask keep working without an environment change.
SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv(
    "DJANGO_SECRET_KEY", "onlyusethisindev"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

# Do not default to "*": it disables Host header validation, allowing password
# reset poisoning (attacker-controlled reset URLs sent to users).
ALLOWED_HOSTS = (os.getenv("ALLOWED_HOSTS") or "localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = [
    k for k in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if len(k) > 0
]

# Application definition
#
# Each of these is a Flask blueprint package; see `shynet.urls` for how they
# are mounted onto the application.

INSTALLED_APPS = [
    "a17t",
    "core",
    "dashboard",
    "analytics",
    "api",
    "accounts",
]

# Templates

TEMPLATE_TRIM_BLOCKS = False
TEMPLATE_AUTO_RELOAD = DEBUG

WSGI_APPLICATION = "shynet.wsgi:application"


# Database

if os.getenv("SQLITE", "False") == "True":
    DATABASES = {
        "default": {
            "ENGINE": "sqlite",
            "NAME": os.environ.get("DB_NAME", "/var/local/shynet/db/db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "postgresql+psycopg2",
            "NAME": os.environ.get("DB_NAME"),
            "USER": os.environ.get("DB_USER"),
            "PASSWORD": os.environ.get("DB_PASSWORD"),
            "HOST": os.environ.get("DB_HOST"),
            "PORT": os.environ.get("DB_PORT"),
            "OPTIONS": {"connect_timeout": 5},
        }
    }

# Solution to removal of Heroku DB Injection
if "DATABASE_URL" in os.environ:
    if "DATABASES" not in locals():
        DATABASES = {}
    url = urlparse.urlparse(os.environ["DATABASE_URL"])

    # Ensure default database exists.
    DATABASES["default"] = DATABASES.get("default", {})

    # Update with environment configuration.
    DATABASES["default"].update(
        {
            "NAME": url.path[1:],
            "USER": url.username,
            "PASSWORD": url.password,
            "HOST": url.hostname,
            "PORT": url.port,
        }
    )
    if url.scheme == "postgres":
        DATABASES["default"]["ENGINE"] = "postgresql+psycopg2"


def _build_database_uri(config):
    """Turn a `DATABASES`-style dict into a SQLAlchemy connection URI."""
    engine = config.get("ENGINE") or "sqlite"
    if engine.startswith("sqlite"):
        name = config.get("NAME") or ":memory:"
        if name == ":memory:":
            return "sqlite://"
        return "sqlite:///" + name
    userinfo = ""
    if config.get("USER"):
        userinfo = urlparse.quote(str(config["USER"]), safe="")
        if config.get("PASSWORD"):
            userinfo += ":" + urlparse.quote(str(config["PASSWORD"]), safe="")
        userinfo += "@"
    netloc = config.get("HOST") or ""
    if config.get("PORT"):
        netloc = f"{netloc}:{config['PORT']}"
    return f"{engine}://{userinfo}{netloc}/{config.get('NAME') or ''}"


SQLALCHEMY_DATABASE_URI = _build_database_uri(DATABASES["default"])
SQLALCHEMY_ENGINE_OPTIONS = (
    {"connect_args": DATABASES["default"]["OPTIONS"]}
    if DATABASES["default"].get("OPTIONS")
    else {}
)

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "core.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "core.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "core.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "core.password_validation.NumericPasswordValidator",
    },
]

# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "filters": {"require_debug_true": {"()": "shynet.logs.RequireDebugTrue"}},
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": [],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "shynet.logs.AdminEmailHandler",
            "filters": [],
        },
    },
    "loggers": {
        "shynet": {"handlers": ["console"], "propagate": True},
        "shynet.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

# Internationalization

LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "en-us")

TIME_ZONE = os.getenv("TIME_ZONE", "America/New_York")

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [os.path.join(BASE_DIR, "translations")]

# Static files (CSS, JavaScript, Images)

STATIC_URL = "/static/"
STATIC_ROOT = "compiledstatic/"
STATICFILES_FINDERS = [
    "shynet.staticfiles.NpmFinder",
    "shynet.staticfiles.AppDirectoriesFinder",
]

# Redis

CACHES = {"default": {"BACKEND": "SimpleCache", "LOCATION": ""}}
if not DEBUG and os.getenv("REDIS_CACHE_LOCATION") is not None:
    CACHES = {
        "default": {
            "BACKEND": "RedisCache",
            "LOCATION": os.getenv("REDIS_CACHE_LOCATION"),
            "KEY_PREFIX": "v1_",  # Increment when migrations occur
        }
    }


# Auth

AUTH_USER_MODEL = "core.User"

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_SUBJECT_PREFIX = ""
ACCOUNT_USER_DISPLAY = lambda k: k.email
ACCOUNT_SIGNUPS_ENABLED = os.getenv("ACCOUNT_SIGNUPS_ENABLED", "False") == "True"
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "none")
# How long (in seconds) an email confirmation or password reset link is valid.
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_SECONDS = 3 * 24 * 60 * 60
ACCOUNT_PASSWORD_RESET_EXPIRE_SECONDS = 3 * 24 * 60 * 60

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"

# How long a signed-in session stays valid, in seconds (two weeks).
SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", "1209600"))

# Addresses that receive the mail_admins log handler's error reports. Empty
# means the handler is a no-op.
ADMINS = []

SITE_ID = 1

INTERNAL_IPS = [
    "127.0.0.1",
]

# Celery

CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "True") == "True"

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_REDIS_SOCKET_TIMEOUT = 15

# GeoIP

MAXMIND_CITY_DB = os.getenv("MAXMIND_CITY_DB", "/etc/GeoLite2-City.mmdb")
MAXMIND_ASN_DB = os.getenv("MAXMIND_ASN_DB", "/etc/GeoLite2-ASN.mmdb")


MESSAGE_TAGS = {
    messages.INFO: "~info",
    messages.WARNING: "~warning",
    messages.ERROR: "~critical",
    messages.SUCCESS: "~positive",
}

# Email

SERVER_EMAIL = os.getenv("SERVER_EMAIL", "Shynet <noreply@shynet.example.com>")
DEFAULT_FROM_EMAIL = SERVER_EMAIL

EMAIL_HOST = None
EMAIL_PORT = 465
EMAIL_HOST_USER = None
EMAIL_HOST_PASSWORD = None
EMAIL_USE_SSL = None
EMAIL_USE_TLS = None

if DEBUG or os.environ.get("EMAIL_HOST") is None:
    EMAIL_BACKEND = "shynet.mail.ConsoleBackend"
else:
    EMAIL_BACKEND = "shynet.mail.SmtpBackend"
    EMAIL_HOST = os.environ.get("EMAIL_HOST")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 465))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
    EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL")
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS")

# NPM

NPM_ROOT_PATH = "../"

NPM_FILE_PATTERNS = {
    "a17t": [os.path.join("dist", "a17t.css"), os.path.join("dist", "tailwind.css")],
    "apexcharts": [os.path.join("dist", "apexcharts.min.js")],
    "litepicker": [
        os.path.join("dist", "nocss", "litepicker.js"),
        os.path.join("dist", "css", "litepicker.css"),
        os.path.join("dist", "plugins", "ranges.js"),
    ],
    "turbolinks": [os.path.join("dist", "turbolinks.js")],
    "stimulus": [os.path.join("dist", "stimulus.umd.js")],
    "inter-ui": [os.path.join("Inter (web)", "*")],
    "@fortawesome": [os.path.join("fontawesome-free", "js", "all.min.js")],
    "datamaps": [os.path.join("dist", "datamaps.world.min.js")],
    "d3": ["d3.min.js"],
    "topojson": [os.path.join("build", "topojson.min.js")],
    "flag-icon-css": [
        os.path.join("css", "flag-icon.min.css"),
        os.path.join("flags", "*"),
    ],
}

# Shynet

# Can everyone create services, or only superusers?
# Note that in the current version of Shynet, being able to edit a service allows
# you to see every registered user on the Shynet instance. This will be changed in
# a future version.
ONLY_SUPERUSERS_CREATE = os.getenv("ONLY_SUPERUSERS_CREATE", "True") == "True"

# Should the script use HTTPS to send the POST requests? The hostname is from
# the Shynet site default. (Edit it using the admin panel.)
SCRIPT_USE_HTTPS = os.getenv("SCRIPT_USE_HTTPS", "True") == "True"

# How frequently should the tracking script "phone home" with a heartbeat, in
# milliseconds?
SCRIPT_HEARTBEAT_FREQUENCY = int(os.getenv("SCRIPT_HEARTBEAT_FREQUENCY", "5000"))

# How much time can elapse between requests from the same user before a new
# session is created, in seconds?
SESSION_MEMORY_TIMEOUT = int(os.getenv("SESSION_MEMORY_TIMEOUT", "1800"))

# Should the Shynet version information be displayed?
SHOW_SHYNET_VERSION = os.getenv("SHOW_SHYNET_VERSION", "True") == "True"

# Should Shynet show third-party icons in the dashboard?
SHOW_THIRD_PARTY_ICONS = os.getenv("SHOW_THIRD_PARTY_ICONS", "True") == "True"

# Should Shynet never collect any IP?
BLOCK_ALL_IPS = os.getenv("BLOCK_ALL_IPS", "False") == "True"

# Include date and service ID in salt?
AGGRESSIVE_HASH_SALTING = os.getenv("AGGRESSIVE_HASH_SALTING", "False") == "True"

# What location url should be linked to in the frontend?
LOCATION_URL = os.getenv(
    "LOCATION_URL", "https://www.openstreetmap.org/?mlat=$LATITUDE&mlon=$LONGITUDE"
)

# How many services should be displayed on dashboard page?
DASHBOARD_PAGE_SIZE = int(os.getenv("DASHBOARD_PAGE_SIZE", "5"))

# Should background bars be scaled to full width?
USE_RELATIVE_MAX_IN_BAR_VISUALIZATION = (
    os.getenv("USE_RELATIVE_MAX_IN_BAR_VISUALIZATION", "True") == "True"
)

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_METHODS = ["GET", "OPTIONS"]
CORS_ALLOW_CREDENTIALS = False
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]
CORS_EXPOSE_HEADERS = []
CORS_PREFLIGHT_MAX_AGE = 86400

# IPWare Precedence Options
IPWARE_META_PRECEDENCE_ORDER = (
    'HTTP_CF_CONNECTING_IP',
    'HTTP_X_FORWARDED_FOR', 'X_FORWARDED_FOR', # client, proxy1, proxy2
    'HTTP_CLIENT_IP',
    'HTTP_X_REAL_IP',
    'HTTP_X_FORWARDED',
    'HTTP_X_CLUSTER_CLIENT_IP',
    'HTTP_FORWARDED_FOR',
    'HTTP_FORWARDED',
    'HTTP_VIA',
    'REMOTE_ADDR',
)

# Security headers; applied by `shynet.middleware`.
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"


def as_flask_config():
    """The subset of the settings above that Flask and its extensions read."""
    return {
        "SECRET_KEY": SECRET_KEY,
        "DEBUG": DEBUG,
        "ALLOWED_HOSTS": ALLOWED_HOSTS,
        "CSRF_TRUSTED_ORIGINS": CSRF_TRUSTED_ORIGINS,
        "SQLALCHEMY_DATABASE_URI": SQLALCHEMY_DATABASE_URI,
        "SQLALCHEMY_ENGINE_OPTIONS": SQLALCHEMY_ENGINE_OPTIONS,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "BABEL_DEFAULT_LOCALE": LANGUAGE_CODE.replace("-", "_"),
        "BABEL_DEFAULT_TIMEZONE": TIME_ZONE,
        "BABEL_TRANSLATION_DIRECTORIES": ";".join(LOCALE_PATHS),
        "CACHE_TYPE": CACHES["default"]["BACKEND"],
        "CACHE_KEY_PREFIX": CACHES["default"].get("KEY_PREFIX", ""),
        "CACHE_REDIS_URL": CACHES["default"].get("LOCATION") or None,
        "MAIL_SERVER": EMAIL_HOST,
        "MAIL_PORT": EMAIL_PORT,
        "MAIL_USERNAME": EMAIL_HOST_USER,
        "MAIL_PASSWORD": EMAIL_HOST_PASSWORD,
        "MAIL_USE_SSL": EMAIL_USE_SSL in (True, "True", "true", "1"),
        "MAIL_USE_TLS": EMAIL_USE_TLS in (True, "True", "true", "1"),
        "MAIL_DEFAULT_SENDER": DEFAULT_FROM_EMAIL,
        "MAIL_SUPPRESS_SEND": EMAIL_BACKEND == "shynet.mail.ConsoleBackend",
        "MAIL_DEBUG": False,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "PERMANENT_SESSION_LIFETIME": SESSION_COOKIE_AGE,
        "REMEMBER_COOKIE_DURATION": SESSION_COOKIE_AGE,
        "REMEMBER_COOKIE_HTTPONLY": True,
        "REMEMBER_COOKIE_SAMESITE": "Lax",
        "DEBUG_TB_INTERCEPT_REDIRECTS": False,
        "WTF_CSRF_TIME_LIMIT": None,
    }
