"""analytics: index Session.last_seen

Ported from analytics/migrations/0004_auto_20210328_1514.py

Revision ID: 0012_analytics_last_seen_indexes
Revises: 0011_core_script_inject_and_first_name
Create Date: 2021-03-28 19:14:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0012_analytics_last_seen_indexes"
down_revision = "0011_core_script_inject_and_first_name"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_analytics_session_last_seen", "analytics_session", ["last_seen"]
    )
    op.create_index(
        "analytics_session_service_last_seen_idx",
        "analytics_session",
        ["service_id", sa.text("last_seen DESC")],
    )


def downgrade():
    op.drop_index(
        "analytics_session_service_last_seen_idx", table_name="analytics_session"
    )
    op.drop_index("ix_analytics_session_last_seen", table_name="analytics_session")

