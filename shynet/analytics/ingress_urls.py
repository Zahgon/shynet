from flask import Blueprint

from shynet.extensions import csrf

from .views import ingress as ingress_views

ingress = Blueprint("ingress", __name__, template_folder="templates")

_pixel_view = ingress_views.PixelView.as_view("endpoint_pixel")
_pixel_id_view = ingress_views.PixelView.as_view("endpoint_pixel_id")
_script_view = csrf.exempt(ingress_views.ScriptView.as_view("endpoint_script"))
_script_id_view = csrf.exempt(ingress_views.ScriptView.as_view("endpoint_script_id"))

ingress.add_url_rule(
    "/<service_uuid>/pixel.gif", view_func=_pixel_view, methods=["GET"]
)
ingress.add_url_rule(
    "/<service_uuid>/script.js",
    view_func=_script_view,
    methods=["GET", "POST"],
)
ingress.add_url_rule(
    "/<service_uuid>/<identifier>/pixel.gif",
    view_func=_pixel_id_view,
    methods=["GET"],
)
ingress.add_url_rule(
    "/<service_uuid>/<identifier>/script.js",
    view_func=_script_id_view,
    methods=["GET", "POST"],
)
