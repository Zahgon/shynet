"""Static file discovery and serving.

This is the replacement for the static files app: `NpmFinder` exposes the
packages listed in `settings.NPM_FILE_PATTERNS` from `node_modules`, and
`AppDirectoriesFinder` exposes each blueprint's `static/` directory. The
`static()` template global builds URLs under `settings.STATIC_URL`, and the
`collectstatic` command copies everything found into `settings.STATIC_ROOT`.

Requested paths reach the finders straight from the URL, so every lookup goes
through `_resolve()`, which refuses to escape the directory it is given.
"""

import fnmatch
import os
import posixpath
import shutil

from flask import Blueprint, abort, send_file
from werkzeug.security import safe_join

from . import settings

static_blueprint = Blueprint("staticfiles", __name__)


def _resolve(root, path):
    """Resolve `path` beneath `root`, or None if it would escape it."""
    candidate = safe_join(root, *path.split("/"))
    if candidate is None or not os.path.isfile(candidate):
        return None
    return candidate


class BaseFinder:
    def find(self, path):
        """Return an absolute filesystem path for `path`, or None."""
        raise NotImplementedError

    def list(self):
        """Yield `(relative_path, absolute_path)` for every matched file."""
        raise NotImplementedError


class NpmFinder(BaseFinder):
    """Exposes whitelisted files from `node_modules` as static assets."""

    def __init__(self):
        self.node_modules_path = os.path.abspath(
            os.path.join(settings.BASE_DIR, settings.NPM_ROOT_PATH, "node_modules")
        )

    def _matches(self, relative_path):
        for package, patterns in settings.NPM_FILE_PATTERNS.items():
            if not (
                relative_path == package or relative_path.startswith(package + "/")
            ):
                continue
            remainder = relative_path[len(package) :].lstrip("/")
            for pattern in patterns:
                pattern = pattern.replace(os.sep, "/")
                if fnmatch.fnmatch(remainder, pattern) or remainder.startswith(
                    pattern.rstrip("*").rstrip("/") + "/"
                ):
                    return True
        return False

    def find(self, path):
        if not self._matches(path):
            return None
        return _resolve(self.node_modules_path, path)

    def list(self):
        if not os.path.isdir(self.node_modules_path):
            return
        for package, patterns in settings.NPM_FILE_PATTERNS.items():
            package_root = os.path.join(self.node_modules_path, *package.split("/"))
            if not os.path.isdir(package_root):
                continue
            for pattern in patterns:
                pattern = pattern.replace(os.sep, "/")
                for absolute in _iter_pattern(package_root, pattern):
                    relative = posixpath.join(
                        package,
                        os.path.relpath(absolute, package_root).replace(os.sep, "/"),
                    )
                    yield relative, absolute


class AppDirectoriesFinder(BaseFinder):
    """Exposes the `static/` directory of every installed blueprint."""

    def __init__(self):
        self.roots = []
        for app in settings.INSTALLED_APPS:
            root = os.path.join(settings.BASE_DIR, app, "static")
            if os.path.isdir(root):
                self.roots.append(root)

    def find(self, path):
        for root in self.roots:
            candidate = _resolve(root, path)
            if candidate is not None:
                return candidate
        return None

    def list(self):
        for root in self.roots:
            for dirpath, _dirnames, filenames in os.walk(root):
                for filename in filenames:
                    absolute = os.path.join(dirpath, filename)
                    relative = os.path.relpath(absolute, root).replace(os.sep, "/")
                    yield relative, absolute


def _iter_pattern(root, pattern):
    """Yield the files under `root` matched by a (possibly globbed) pattern."""
    parts = pattern.split("/")
    candidate = os.path.join(root, *parts)
    if "*" not in pattern and "?" not in pattern:
        if os.path.isfile(candidate):
            yield candidate
        elif os.path.isdir(candidate):
            for dirpath, _dirnames, filenames in os.walk(candidate):
                for filename in filenames:
                    yield os.path.join(dirpath, filename)
        return
    directory = os.path.join(root, *parts[:-1])
    if not os.path.isdir(directory):
        return
    for name in sorted(os.listdir(directory)):
        if not fnmatch.fnmatch(name, parts[-1]):
            continue
        absolute = os.path.join(directory, name)
        if os.path.isfile(absolute):
            yield absolute
        elif os.path.isdir(absolute):
            for dirpath, _dirnames, filenames in os.walk(absolute):
                for filename in filenames:
                    yield os.path.join(dirpath, filename)


_finders = None


def get_finders():
    global _finders
    if _finders is None:
        _finders = []
        for path in settings.STATICFILES_FINDERS:
            module_name, class_name = path.rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            _finders.append(getattr(module, class_name)())
    return _finders


def find(path):
    for finder in get_finders():
        result = finder.find(path)
        if result is not None:
            return result
    return None


def static(path):
    """Build the URL for a static file, as the `{% static %}` tag used to."""
    return posixpath.join(settings.STATIC_URL, str(path).lstrip("/"))


@static_blueprint.route(settings.STATIC_URL + "<path:filename>")
def serve(filename):
    absolute = find(filename)
    if absolute is None:
        abort(404)
    return send_file(absolute, conditional=True)


def collect(destination=None, clear=False):
    """Copy every discoverable static file into `STATIC_ROOT`."""
    destination = destination or os.path.join(settings.BASE_DIR, settings.STATIC_ROOT)
    if clear and os.path.isdir(destination):
        shutil.rmtree(destination)
    collected = 0
    for finder in get_finders():
        for relative, absolute in finder.list():
            target = os.path.join(destination, *relative.split("/"))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(absolute, target)
            collected += 1
    return collected, destination
