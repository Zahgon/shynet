import base64
import json
from urllib.parse import urlparse

from flask import Response, make_response, render_template, request, url_for
from flask.views import MethodView
from sqlalchemy import select
from sqlalchemy.exc import StatementError

from core.models import Service
from shynet import settings, timezone
from shynet.cache import cache
from shynet.exceptions import ObjectDoesNotExist
from shynet.extensions import db
from shynet.ipware import get_client_ip

from ..tasks import ingress_request


def ingress(request, service_uuid, identifier, tracker, payload):
    time = timezone.now()
    client_ip, is_routable = get_client_ip(request)
    location = request.headers.get("Referer", "").strip()
    user_agent = request.headers.get("User-Agent", "").strip()
    dnt = request.headers.get("DNT", "0").strip() == "1"
    gpc = request.headers.get("Sec-GPC", "0").strip() == "1"
    if gpc or dnt:
        dnt = True

    ingress_request.delay(
        service_uuid,
        tracker,
        time,
        payload,
        client_ip,
        location,
        user_agent,
        dnt=dnt,
        identifier=identifier,
    )


class ValidateServiceOriginsMixin:
    def dispatch_request(self, *args, **kwargs):
        try:
            service_uuid = kwargs.get("service_uuid")
            origins = cache.get(f"service_origins_{service_uuid}")

            if origins is None:
                service = db.session.scalar(
                    select(Service).where(Service.uuid == service_uuid)
                )
                if service is None:
                    raise ObjectDoesNotExist()
                origins = service.origins
                cache.set(f"service_origins_{service_uuid}", origins, timeout=3600)

            allow_origin = "*"

            if origins != "*":
                remote_origin = request.headers.get("Origin")
                if (
                    remote_origin is None
                    and request.headers.get("Referer") is not None
                ):
                    parsed = urlparse(request.headers.get("Referer"))
                    remote_origin = f"{parsed.scheme}://{parsed.netloc}".lower()
                origins = [origin.strip().lower() for origin in origins.split(",")]
                if remote_origin in origins:
                    allow_origin = remote_origin
                else:
                    return Response(status=403)

            resp = make_response(super().dispatch_request(*args, **kwargs))
            resp.headers["Access-Control-Allow-Origin"] = allow_origin
            resp.headers["Access-Control-Allow-Methods"] = "GET,HEAD,OPTIONS,POST"
            resp.headers[
                "Access-Control-Allow-Headers"
            ] = "Origin, X-Requested-With, Content-Type, Accept, Authorization, Referer"
            return resp
        except ObjectDoesNotExist:
            db.session.rollback()
            return Response(status=404)
        except (ValueError, StatementError):
            # A malformed service UUID.
            db.session.rollback()
            return Response(status=400)


class PixelView(ValidateServiceOriginsMixin, MethodView):
    # Fallback view to serve an unobtrusive 1x1 transparent tracking pixel for browsers with
    # JavaScript disabled.
    def get(self, *args, **kwargs):
        # Extract primary data
        ingress(
            request,
            kwargs.get("service_uuid"),
            kwargs.get("identifier", "") or "",
            "PIXEL",
            {},
        )

        data = base64.b64decode(
            "R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="
        )
        resp = Response(data, mimetype="image/gif")
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp


class ScriptView(ValidateServiceOriginsMixin, MethodView):
    def get(self, *args, **kwargs):
        protocol = "https" if settings.SCRIPT_USE_HTTPS else "http"
        endpoint = (
            url_for(
                "ingress.endpoint_script",
                service_uuid=kwargs.get("service_uuid"),
            )
            if kwargs.get("identifier") is None
            else url_for(
                "ingress.endpoint_script_id",
                service_uuid=kwargs.get("service_uuid"),
                identifier=kwargs.get("identifier"),
            )
        )
        heartbeat_frequency = settings.SCRIPT_HEARTBEAT_FREQUENCY
        dnt = request.headers.get("DNT", "0").strip() == "1"
        service_uuid = kwargs.get("service_uuid")
        service = db.session.scalar(
            select(Service).where(
                Service.uuid == service_uuid, Service.status == Service.ACTIVE
            )
        )
        if service is None:
            raise ObjectDoesNotExist()
        body = render_template(
            "analytics/scripts/page.js",
            **dict(
                {
                    "endpoint": endpoint,
                    "protocol": protocol,
                    "heartbeat_frequency": heartbeat_frequency,
                    "script_inject": self.get_script_inject(kwargs),
                    "dnt": dnt and service.respect_dnt,
                }
            ),
        )
        response = Response(body, mimetype="application/javascript")

        response.headers["Cache-Control"] = "public, max-age=31536000"  # 1 year
        return response

    def post(self, *args, **kwargs):
        payload = json.loads(request.get_data())
        ingress(
            request,
            kwargs.get("service_uuid"),
            kwargs.get("identifier", "") or "",
            "JS",
            payload,
        )
        return Response(
            json.dumps({"status": "OK"}), mimetype="application/json"
        )

    def get_script_inject(self, kwargs):
        service_uuid = kwargs.get("service_uuid")
        script_inject = cache.get(f"script_inject_{service_uuid}")
        if script_inject is None:
            service = db.session.scalar(
                select(Service).where(Service.uuid == service_uuid)
            )
            if service is None:
                raise ObjectDoesNotExist()
            script_inject = service.script_inject
            cache.set(f"script_inject_{service_uuid}", script_inject, timeout=3600)
        return script_inject
