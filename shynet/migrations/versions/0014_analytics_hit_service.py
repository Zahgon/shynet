"""analytics: denormalise the service onto Hit

Ported from analytics/migrations/0006_hit_service.py

Revision ID: 0014_analytics_hit_service
Revises: 0013_analytics_hit_last_seen_load_time_indexes
Create Date: 2021-03-28 19:36:00

"""
import sqlalchemy as sa
from alembic import op

from shynet.dbtypes import GUID

revision = "0014_analytics_hit_service"
down_revision = "0013_analytics_hit_last_seen_load_time_indexes"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("analytics_hit") as batch_op:
        batch_op.add_column(sa.Column("service_id", GUID(), nullable=True))
        batch_op.create_foreign_key(
            "analytics_hit_service_id_fkey",
            "core_service",
            ["service_id"],
            ["uuid"],
            ondelete="CASCADE",
        )
    op.create_index("ix_analytics_hit_service_id", "analytics_hit", ["service_id"])

    # Backfill each hit's service from its session.
    op.execute(
        """
        UPDATE analytics_hit
        SET service_id = (
            SELECT analytics_session.service_id
            FROM analytics_session
            WHERE analytics_session.uuid = analytics_hit.session_id
        )
        """
    )

    with op.batch_alter_table("analytics_hit") as batch_op:
        batch_op.alter_column("service_id", existing_type=GUID(), nullable=False)


def downgrade():
    op.drop_index("ix_analytics_hit_service_id", table_name="analytics_hit")
    with op.batch_alter_table("analytics_hit") as batch_op:
        batch_op.drop_constraint(
            "analytics_hit_service_id_fkey", type_="foreignkey"
        )
        batch_op.drop_column("service_id")
