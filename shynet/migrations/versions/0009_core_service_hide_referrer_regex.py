"""core: add Service.hide_referrer_regex

Ported from core/migrations/0006_service_hide_referrer_regex.py

Revision ID: 0009_core_service_hide_referrer_regex
Revises: 0008_core_service_ignored_ips
Create Date: 2020-05-07 21:23:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0009_core_service_hide_referrer_regex"
down_revision = "0008_core_service_ignored_ips"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "core_service",
        sa.Column(
            "hide_referrer_regex", sa.Text(), nullable=False, server_default=""
        ),
    )
    with op.batch_alter_table("core_service") as batch_op:
        batch_op.alter_column(
            "hide_referrer_regex",
            existing_type=sa.Text(),
            existing_nullable=False,
            server_default=None,
        )


def downgrade():
    op.drop_column("core_service", "hide_referrer_regex")

