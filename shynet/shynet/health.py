"""Health checks.

`/healthz/` reports whether the database and cache are reachable; passing
`?format=json` returns the same information as JSON (this is what the container
health check uses).
"""

from flask import Blueprint, jsonify, render_template_string, request

from .cache import cache
from .extensions import db

health = Blueprint("health_check", __name__)

_TEMPLATE = """<!DOCTYPE html>
<html><head><title>Health check</title></head><body>
<table><thead><tr><th>Service</th><th>Status</th><th>Time</th></tr></thead>
<tbody>
{% for name, status in results.items() %}
<tr><td>{{ name }}</td><td>{{ status }}</td></tr>
{% endfor %}
</tbody></table>
</body></html>"""


def _check_database():
    from sqlalchemy import text

    db.session.execute(text("SELECT 1"))
    return "working"


def _check_cache():
    cache.set("health_check", "working", timeout=10)
    if cache.get("health_check") != "working":
        raise RuntimeError("Cache did not return the value that was set")
    return "working"


CHECKS = {
    "DatabaseBackend": _check_database,
    "CacheBackend": _check_cache,
}


@health.route("/")
def index():
    results = {}
    healthy = True
    for name, check in CHECKS.items():
        try:
            results[name] = check()
        except Exception as exception:  # noqa: BLE001 - surfaced in the response
            results[name] = f"unavailable: {exception}"
            healthy = False

    status_code = 200 if healthy else 500
    if request.args.get("format") == "json":
        return jsonify(results), status_code
    return render_template_string(_TEMPLATE, results=results), status_code
