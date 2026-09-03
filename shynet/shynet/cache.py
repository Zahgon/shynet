"""Cache access.

A thin wrapper around Flask-Caching that keeps the `get`/`set`/`touch`/`delete`
interface Shynet's tasks and views were written against.
"""

from .extensions import cache as _cache


class CacheProxy:
    def get(self, key, default=None):
        value = _cache.get(key)
        return default if value is None else value

    def set(self, key, value, timeout=None):
        return _cache.set(key, value, timeout=timeout)

    def add(self, key, value, timeout=None):
        return _cache.add(key, value, timeout=timeout)

    def touch(self, key, timeout=None):
        """Re-set an existing key with a fresh timeout; no-op when absent."""
        value = _cache.get(key)
        if value is None:
            return False
        _cache.set(key, value, timeout=timeout)
        return True

    def delete(self, key):
        return _cache.delete(key)

    def clear(self):
        return _cache.clear()


cache = CacheProxy()
