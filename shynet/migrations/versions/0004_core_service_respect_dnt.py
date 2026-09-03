"""core: add Service.respect_dnt

Ported from core/migrations/0003_service_respect_dnt.py

Revision ID: 0004_core_service_respect_dnt
Revises: 0003_core_service_ordering
Create Date: 2020-04-22 17:03:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0004_core_service_respect_dnt"
down_revision = "0003_core_service_ordering"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "core_service",
        sa.Column(
            "respect_dnt", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    with op.batch_alter_table("core_service") as batch_op:
        batch_op.alter_column(
            "respect_dnt",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=None,
        )


def downgrade():
    op.drop_column("core_service", "respect_dnt")

