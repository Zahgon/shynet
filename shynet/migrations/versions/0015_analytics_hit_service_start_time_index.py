"""analytics: index Hit by service and start time

Ported from analytics/migrations/0007_auto_20210328_1634.py

Revision ID: 0015_analytics_hit_service_start_time_index
Revises: 0014_analytics_hit_service
Create Date: 2021-03-28 20:34:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0015_analytics_hit_service_start_time_index"
down_revision = "0014_analytics_hit_service"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "analytics_hit_service_start_time_idx",
        "analytics_hit",
        ["service_id", sa.text("start_time DESC")],
    )


def downgrade():
    op.drop_index("analytics_hit_service_start_time_idx", table_name="analytics_hit")

