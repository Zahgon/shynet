"""core: add Service.ignore_robots

Ported from core/migrations/0007_service_ignore_robots.py

Revision ID: 0010_core_service_ignore_robots
Revises: 0009_core_service_hide_referrer_regex
Create Date: 2020-06-15 16:16:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0010_core_service_ignore_robots"
down_revision = "0009_core_service_hide_referrer_regex"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "core_service",
        sa.Column(
            "ignore_robots", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    with op.batch_alter_table("core_service") as batch_op:
        batch_op.alter_column(
            "ignore_robots",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=None,
        )


def downgrade():
    op.drop_column("core_service", "ignore_robots")

