"""core: the site (domain and whitelabel name) table

Ported from the sites framework's initial migrations

Revision ID: 0021_core_site
Revises: 0020_analytics_verbose_names
Create Date: 2022-06-24 11:44:00

"""
import sqlalchemy as sa
from alembic import op

from shynet.dbtypes import big_integer

revision = "0021_core_site"
down_revision = "0020_analytics_verbose_names"
branch_labels = None
depends_on = None


def upgrade():
    site = op.create_table(
        "core_site",
        sa.Column("id", big_integer(), autoincrement=True, nullable=False),
        sa.Column("domain", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain", name="core_site_domain_key"),
    )
    op.bulk_insert(
        site, [{"id": 1, "domain": "example.com", "name": "example.com"}]
    )


def downgrade():
    op.drop_table("core_site")

