"""Command discovery and the framework-level commands.

Each installed app can put click commands in `<app>/management/commands/*.py`
(exposing a `command` object); they are attached to the app's CLI here, along
with `collectstatic`, `compilemessages` and `migrate`.
"""

import importlib
import os
import pkgutil

import click
from flask.cli import with_appcontext

from . import settings, staticfiles


@click.command("collectstatic")
@click.option(
    "--noinput",
    "--no-input",
    "noinput",
    is_flag=True,
    default=False,
    help="Do not prompt for confirmation.",
)
@click.option("--clear", is_flag=True, default=False, help="Clear the target first.")
def collectstatic(noinput, clear):
    """Collect every static file into STATIC_ROOT."""
    count, destination = staticfiles.collect(clear=clear)
    click.secho(f"{count} static files copied to '{destination}'.", fg="green")


@click.command("compilemessages")
def compilemessages():
    """Compile the .po translation catalogs into .mo files."""
    from babel.messages.mofile import write_mo
    from babel.messages.pofile import read_po

    compiled = 0
    for locale_path in settings.LOCALE_PATHS:
        for dirpath, _dirnames, filenames in os.walk(locale_path):
            for filename in filenames:
                if not filename.endswith(".po"):
                    continue
                po_path = os.path.join(dirpath, filename)
                mo_path = po_path[: -len(".po")] + ".mo"
                with open(po_path, "rb") as po_file:
                    catalog = read_po(po_file)
                with open(mo_path, "wb") as mo_file:
                    write_mo(mo_file, catalog)
                compiled += 1
    click.secho(f"Compiled {compiled} message catalog(s).", fg="green")


@click.command("migrate")
@click.argument("revision", default="head")
@with_appcontext
def migrate_command(revision):
    """Apply database migrations (alias for `db upgrade`)."""
    from flask_migrate import upgrade

    upgrade(revision=revision)


def _iter_app_commands():
    for app_name in settings.INSTALLED_APPS:
        package_name = f"{app_name}.management.commands"
        try:
            package = importlib.import_module(package_name)
        except ModuleNotFoundError:
            continue
        for _finder, name, _ispkg in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"{package_name}.{name}")
            command = getattr(module, "command", None)
            if command is not None:
                yield command


def register(app):
    app.cli.add_command(collectstatic)
    app.cli.add_command(compilemessages)
    app.cli.add_command(migrate_command)
    for command in _iter_app_commands():
        app.cli.add_command(command)
