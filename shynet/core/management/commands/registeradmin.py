import uuid

import click
from flask.cli import with_appcontext

from core.hashers import get_random_string
from core.models import User


@click.command("registeradmin")
@click.argument("email", type=str)
@with_appcontext
def command(email):
    """Creates an admin user with an auto-generated password"""
    password = get_random_string(10)
    User.create_superuser(str(uuid.uuid4()), email=email, password=password)
    click.secho("Successfully created a Shynet superuser", fg="green")
    click.echo(f"Email address: {email}")
    click.echo(f"Password: {password}")
