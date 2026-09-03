import click
from flask.cli import with_appcontext

from core.models import Site
from shynet import settings
from shynet.extensions import db


@click.command("whitelabel")
@click.argument("name", type=str)
@with_appcontext
def command(name):
    """Configures a Shynet whitelabel"""
    site = db.session.get(Site, settings.SITE_ID)
    site.name = name
    db.session.add(site)
    db.session.commit()
    click.secho(f"Successfully set the whitelabel to '{name}'", fg="green")
