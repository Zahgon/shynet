"""analytics: allow Session.ip to be null

Ported from analytics/migrations/0003_auto_20200502_1227.py

Revision ID: 0007_analytics_session_ip_nullable
Revises: 0006_analytics_hit_tracker_choices
Create Date: 2020-05-02 16:27:00

"""
import sqlalchemy as sa
from alembic import op

from shynet.dbtypes import IPAddress

revision = "0007_analytics_session_ip_nullable"
down_revision = "0006_analytics_hit_tracker_choices"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("analytics_session") as batch_op:
        batch_op.alter_column(
            "ip", existing_type=IPAddress(), nullable=True
        )


def downgrade():
    with op.batch_alter_table("analytics_session") as batch_op:
        batch_op.alter_column(
            "ip", existing_type=IPAddress(), nullable=False
        )

