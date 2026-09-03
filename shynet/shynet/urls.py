"""shynet URL Configuration

Blueprints are mounted onto the application here. Each installed app exposes a
blueprint whose endpoints keep the names the templates use, so `url_for` reads
the same way the old `{% url %}` tags did (`dashboard.service`,
`ingress.endpoint_pixel`, `core.index`, `api.services`, ...).
"""

from .health import health
from .staticfiles import static_blueprint


def register_blueprints(app):
    from a17t.views import a17t as a17t_blueprint
    from accounts.views import accounts as accounts_blueprint
    from analytics.ingress_urls import ingress as ingress_blueprint
    from api.urls import api as api_blueprint
    from core.urls import core as core_blueprint
    from dashboard.urls import dashboard as dashboard_blueprint

    app.register_blueprint(static_blueprint)
    app.register_blueprint(accounts_blueprint, url_prefix="/accounts")
    app.register_blueprint(ingress_blueprint, url_prefix="/ingress")
    app.register_blueprint(dashboard_blueprint, url_prefix="/dashboard")
    app.register_blueprint(health, url_prefix="/healthz")
    app.register_blueprint(a17t_blueprint)
    app.register_blueprint(core_blueprint, url_prefix="")
    app.register_blueprint(api_blueprint, url_prefix="/api/v1")
