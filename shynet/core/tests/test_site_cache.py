"""The current site is read on every request, so it must not be re-queried."""

from sqlalchemy import event
from sqlalchemy.engine import Engine

from core.models import Site
from shynet.extensions import db


def _count_site_queries(fn):
    statements = []

    def _listen(conn, cursor, statement, params, context, executemany):
        if "core_site" in statement:
            statements.append(statement)

    event.listen(Engine, "before_cursor_execute", _listen)
    try:
        fn()
    finally:
        event.remove(Engine, "before_cursor_execute", _listen)
    return len(statements)


def test_current_site_is_cached_across_requests(app, client):
    """
    GIVEN: Repeated requests to a tracking endpoint
    WHEN: Each one attaches the current site
    THEN: The site should be loaded once, not once per request
    """
    Site.clear_cache()

    def make_requests():
        for _ in range(10):
            client.get("/accounts/login/")

    assert _count_site_queries(make_requests) <= 1


def test_writing_a_site_clears_the_cache(app, client):
    """
    GIVEN: A cached site
    WHEN: Its whitelabel name is changed
    THEN: The new name should be served immediately
    """
    Site.clear_cache()
    client.get("/accounts/login/")

    site = db.session.get(Site, 1)
    site.name = "Renamed Instance"
    db.session.add(site)
    db.session.commit()

    assert b"Renamed Instance" in client.get("/accounts/login/").data
