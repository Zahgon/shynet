import click
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from core.models import Site, User
from shynet.extensions import db


def check_migrations():
    """True when there are migrations still to apply (or the DB is unreachable)."""
    from alembic.migration import MigrationContext
    from alembic.script import ScriptDirectory

    try:
        config = current_app.extensions["migrate"].migrate.get_config()
        script = ScriptDirectory.from_config(config)
        with db.engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current = context.get_current_revision()
    except OperationalError:
        # DB_NAME database not found?
        return True
    except Exception:
        # No databases are configured (or the dummy one)
        return True

    return current != script.get_current_head()


@click.command("startup_checks")
@with_appcontext
def command():
    """Internal command to perform startup checks."""
    migration = check_migrations()

    admin, whitelabel = [True] * 2
    if not migration:
        admin = not db.session.scalar(select(func.count()).select_from(User))
        whitelabel = not db.session.scalar(
            select(func.count())
            .select_from(Site)
            .where(
                Site.name.is_not(None),
                Site.name != "",
                Site.name != "example.com",
            )
        )

    click.secho(f"{migration} {bool(admin)} {bool(whitelabel)}", fg="green")
