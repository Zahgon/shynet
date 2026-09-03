"""analytics: add Session.is_bounce

Ported from analytics/migrations/0008_session_is_bounce.py

Revision ID: 0016_analytics_session_is_bounce
Revises: 0015_analytics_hit_service_start_time_index
Create Date: 2021-03-28 21:38:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0016_analytics_session_is_bounce"
down_revision = "0015_analytics_hit_service_start_time_index"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "analytics_session",
        sa.Column(
            "is_bounce", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    with op.batch_alter_table("analytics_session") as batch_op:
        batch_op.alter_column(
            "is_bounce",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=None,
        )
    op.create_index(
        "ix_analytics_session_is_bounce", "analytics_session", ["is_bounce"]
    )


def downgrade():
    op.drop_index("ix_analytics_session_is_bounce", table_name="analytics_session")
    op.drop_column("analytics_session", "is_bounce")

