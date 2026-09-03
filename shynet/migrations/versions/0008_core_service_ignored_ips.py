"""core: add Service.ignored_ips

Ported from core/migrations/0005_service_ignored_ips.py

Revision ID: 0008_core_service_ignored_ips
Revises: 0007_analytics_session_ip_nullable
Create Date: 2020-05-07 20:28:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0008_core_service_ignored_ips"
down_revision = "0007_analytics_session_ip_nullable"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "core_service",
        sa.Column("ignored_ips", sa.Text(), nullable=False, server_default=""),
    )
    with op.batch_alter_table("core_service") as batch_op:
        batch_op.alter_column(
            "ignored_ips",
            existing_type=sa.Text(),
            existing_nullable=False,
            server_default=None,
        )


def downgrade():
    op.drop_column("core_service", "ignored_ips")

