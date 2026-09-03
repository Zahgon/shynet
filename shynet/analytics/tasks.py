import ipaddress
import logging
from hashlib import sha256

import geoip2.database
import user_agents
from sqlalchemy import select

from core.models import Service
from shynet import settings, timezone
from shynet.cache import cache
from shynet.exceptions import ObjectDoesNotExist
from shynet.celery import app as celery_app
from shynet.extensions import db

from .models import Hit, Session

log = logging.getLogger(__name__)

_geoip2_city_reader = None
_geoip2_asn_reader = None


def _geoip2_lookup(ip):
    global _geoip2_city_reader, _geoip2_asn_reader
    try:
        if settings.MAXMIND_CITY_DB == None or settings.MAXMIND_ASN_DB == None:
            return None
        if _geoip2_city_reader == None or _geoip2_asn_reader == None:
            _geoip2_city_reader = geoip2.database.Reader(settings.MAXMIND_CITY_DB)
            _geoip2_asn_reader = geoip2.database.Reader(settings.MAXMIND_ASN_DB)
        city_results = _geoip2_city_reader.city(ip)
        asn_results = _geoip2_asn_reader.asn(ip)
        return {
            "asn": asn_results.autonomous_system_organization,
            "country": city_results.country.iso_code,
            "longitude": city_results.location.longitude,
            "latitude": city_results.location.latitude,
            "time_zone": city_results.location.time_zone,
        }
    except geoip2.errors.AddressNotFoundError:
        return {}
    except FileNotFoundError as e:
        log.exception("Unable to perform GeoIP lookup: %s", e)
        return {}


@celery_app.task
def ingress_request(
    service_uuid,
    tracker,
    time,
    payload,
    ip,
    location,
    user_agent,
    dnt=False,
    identifier="",
):
    try:
        service = db.session.scalar(
            select(Service).where(
                Service.uuid == service_uuid, Service.status == Service.ACTIVE
            )
        )
        if service is None:
            raise ObjectDoesNotExist(
                f"No active service with uuid {service_uuid}"
            )
        log.debug(f"Linked to service {service}")

        if dnt and service.respect_dnt:
            log.debug("Ignoring because of DNT or GPC")
            return

        try:
            remote_ip = ipaddress.ip_network(ip)
            for ignored_network in service.get_ignored_networks():
                if (
                    ignored_network.version == remote_ip.version
                    and ignored_network.supernet_of(remote_ip)
                ):
                    log.debug("Ignoring because of ignored IP")
                    return
        except ValueError as e:
            log.exception(e)

        # Validate payload
        if payload.get("loadTime", 1) <= 0:
            payload["loadTime"] = None

        association_id_hash = sha256()
        association_id_hash.update(str(ip).encode("utf-8"))
        association_id_hash.update(str(user_agent).encode("utf-8"))
        if settings.AGGRESSIVE_HASH_SALTING:
            association_id_hash.update(str(service.pk).encode("utf-8"))
            association_id_hash.update(
                str(timezone.now().date().isoformat()).encode("utf-8")
            )
        session_cache_path = (
            f"session_association_{service.pk}_{association_id_hash.hexdigest()}"
        )

        # Create or update session
        session = None
        if cache.get(session_cache_path) is not None:
            cache.touch(session_cache_path, settings.SESSION_MEMORY_TIMEOUT)
            session = db.session.scalar(
                select(Session).where(
                    Session.uuid == cache.get(session_cache_path),
                    Session.service_id == service.uuid,
                )
            )
        if session is None:
            initial = True

            log.debug("Cannot link to existing session; creating a new one...")

            ip_data = _geoip2_lookup(ip)
            log.debug(f"Found geoip2 data...")

            ua = user_agents.parse(user_agent)
            device_type = "OTHER"
            if (
                ua.is_bot
                or (ua.browser.family or "").strip().lower() == "googlebot"
                or (ua.device.family or ua.device.model or "").strip().lower()
                == "spider"
            ):
                device_type = "ROBOT"
            elif ua.is_mobile:
                device_type = "PHONE"
            elif ua.is_tablet:
                device_type = "TABLET"
            elif ua.is_pc:
                device_type = "DESKTOP"
            if device_type == "ROBOT" and service.ignore_robots:
                return
            session = Session(
                service_id=service.uuid,
                ip=ip if service.collect_ips and not settings.BLOCK_ALL_IPS else None,
                user_agent=user_agent,
                identifier=identifier.strip(),
                browser=ua.browser.family or "",
                device=ua.device.family or ua.device.model or "",
                device_type=device_type,
                start_time=time,
                last_seen=time,
                os=ua.os.family or "",
                asn=ip_data.get("asn") or "",
                country=ip_data.get("country") or "",
                longitude=ip_data.get("longitude"),
                latitude=ip_data.get("latitude"),
                time_zone=ip_data.get("time_zone") or "",
            )
            db.session.add(session)
            db.session.commit()
            cache.set(
                session_cache_path, str(session.pk), timeout=settings.SESSION_MEMORY_TIMEOUT
            )
        else:
            initial = False

            log.debug("Updating old session with new data...")

            # Update last seen time
            session.last_seen = time
            if session.identifier == "" and identifier.strip() != "":
                session.identifier = identifier.strip()
            db.session.add(session)
            db.session.commit()

        # Create or update hit
        idempotency = payload.get("idempotency")
        idempotency_path = f"hit_idempotency_{idempotency}"
        hit = None

        if idempotency is not None:
            if cache.get(idempotency_path) is not None:
                cache.touch(idempotency_path, settings.SESSION_MEMORY_TIMEOUT)
                hit = db.session.scalar(
                    select(Hit).where(
                        Hit.id == cache.get(idempotency_path),
                        Hit.session_id == session.uuid,
                    )
                )
                if hit is not None:
                    # There is an existing hit with an identical idempotency key. That means
                    # this is a heartbeat.
                    log.debug("Hit is a heartbeat; updating old hit with new data...")
                    hit.heartbeats += 1
                    hit.last_seen = time
                    db.session.add(hit)
                    db.session.commit()

        if hit is None:
            log.debug("Hit is a page load; creating new hit...")
            # There is no existing hit; create a new one
            hit = Hit(
                session_id=session.uuid,
                initial=initial,
                tracker=tracker,
                # At first, location is given by the HTTP referrer. Some browsers
                # will send the source of the script, however, so we allow JS payloads
                # to include the location.
                location=payload.get("location", location),
                referrer=payload.get("referrer", ""),
                load_time=payload.get("loadTime"),
                start_time=time,
                last_seen=time,
                service_id=service.uuid,
            )
            db.session.add(hit)
            db.session.commit()

            # Recalculate whether the session is a bounce
            session.recalculate_bounce()

            # Set idempotency (if applicable)
            if idempotency is not None:
                cache.set(
                    idempotency_path, hit.pk, timeout=settings.SESSION_MEMORY_TIMEOUT
                )
    except Exception as e:
        db.session.rollback()
        log.exception(e)
        print(e)
        raise e
