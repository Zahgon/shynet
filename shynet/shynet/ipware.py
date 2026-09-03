"""Client IP detection.

A port of the `get_client_ip` helper Shynet used, honouring
`settings.IPWARE_META_PRECEDENCE_ORDER`: the first routable address wins;
failing that, the best non-routable one, preferring anything over loopback.
The address is returned as it was received (minus any port), not re-serialised,
so IPv4-mapped IPv6 forms survive intact.
"""

import ipaddress


def _parse(ip_str):
    try:
        return ipaddress.ip_address(ip_str)
    except ValueError:
        return None


def _unmap(ip):
    """Unwrap `::ffff:1.2.3.4` so it is classified as the IPv4 address it is."""
    mapped = getattr(ip, "ipv4_mapped", None)
    return mapped if mapped is not None else ip


def _strip_port(chunk):
    if chunk.startswith("[") and "]" in chunk:
        return chunk[1 : chunk.index("]")]
    if chunk.count(":") == 1 and "." in chunk:
        return chunk.split(":")[0]
    return chunk


def _candidates(environ):
    from . import settings

    for key in settings.IPWARE_META_PRECEDENCE_ORDER:
        value = environ.get(key)
        if not value:
            continue
        for chunk in str(value).split(","):
            chunk = chunk.strip().lower()
            if chunk:
                yield _strip_port(chunk)


def get_client_ip(request):
    """Return `(ip, is_routable)` for the given request, or `(None, False)`."""
    best_matched_ip = None
    best_matched_address = None
    for candidate in _candidates(request.environ):
        address = _parse(candidate)
        if address is None:
            continue
        address = _unmap(address)
        if address.is_global:
            return candidate, True
        if best_matched_ip is None or (
            best_matched_address.is_loopback and not address.is_loopback
        ):
            best_matched_ip, best_matched_address = candidate, address
    if best_matched_ip is not None:
        return best_matched_ip, False
    return None, False
