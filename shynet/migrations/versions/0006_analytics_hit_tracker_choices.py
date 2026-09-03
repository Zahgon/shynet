"""analytics: restrict Hit.tracker to the known trackers

Ported from analytics/migrations/0002_auto_20200415_1742.py

Revision ID: 0006_analytics_hit_tracker_choices
Revises: 0005_core_service_collect_ips
Create Date: 2020-04-15 21:42:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0006_analytics_hit_tracker_choices"
down_revision = "0005_core_service_collect_ips"
branch_labels = None
depends_on = None


def upgrade():
    # The choices are enforced by the model, not the database; no schema change.
    pass


def downgrade():
    pass

