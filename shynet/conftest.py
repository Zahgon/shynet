"""Shared test fixtures.

Each test runs against a throwaway SQLite database with the schema created from
the models, inside an application context.
"""

import os

os.environ.setdefault("SQLITE", "True")
os.environ.setdefault("DB_NAME", ":memory:")

import pytest

from shynet import settings
from shynet.app import create_app
from shynet.extensions import db


@pytest.fixture()
def app():
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SQLALCHEMY_ENGINE_OPTIONS": {},
            "ALLOWED_HOSTS": ["*"],
        }
    )
    with application.app_context():
        db.create_all()
        _create_default_site()
        yield application
        db.session.remove()
        db.drop_all()


def _create_default_site():
    from core.models import Site

    if db.session.get(Site, settings.SITE_ID) is None:
        db.session.add(
            Site(id=settings.SITE_ID, domain="example.com", name="example.com")
        )
        db.session.commit()


@pytest.fixture()
def client(app):
    return app.test_client()
