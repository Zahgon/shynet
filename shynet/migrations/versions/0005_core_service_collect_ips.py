"""core: add Service.collect_ips

Ported from core/migrations/0004_service_collect_ips.py

Revision ID: 0005_core_service_collect_ips
Revises: 0004_core_service_respect_dnt
Create Date: 2020-05-02 16:22:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0005_core_service_collect_ips"
down_revision = "0004_core_service_respect_dnt"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "core_service",
        sa.Column(
            "collect_ips", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    with op.batch_alter_table("core_service") as batch_op:
        batch_op.alter_column(
            "collect_ips",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=None,
        )


def downgrade():
    op.drop_column("core_service", "collect_ips")

