"""analytics: index Hit.last_seen and Hit.load_time

Ported from analytics/migrations/0005_auto_20210328_1518.py

Revision ID: 0013_analytics_hit_last_seen_load_time_indexes
Revises: 0012_analytics_last_seen_indexes
Create Date: 2021-03-28 19:18:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0013_analytics_hit_last_seen_load_time_indexes"
down_revision = "0012_analytics_last_seen_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_analytics_hit_last_seen", "analytics_hit", ["last_seen"])
    op.create_index("ix_analytics_hit_load_time", "analytics_hit", ["load_time"])


def downgrade():
    op.drop_index("ix_analytics_hit_load_time", table_name="analytics_hit")
    op.drop_index("ix_analytics_hit_last_seen", table_name="analytics_hit")

