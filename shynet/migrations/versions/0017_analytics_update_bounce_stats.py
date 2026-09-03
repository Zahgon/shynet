"""analytics: backfill Session.is_bounce

Ported from analytics/migrations/0009_auto_20210329_1100.py

Revision ID: 0017_analytics_update_bounce_stats
Revises: 0016_analytics_session_is_bounce
Create Date: 2021-03-29 15:00:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0017_analytics_update_bounce_stats"
down_revision = "0016_analytics_session_is_bounce"
branch_labels = None
depends_on = None


def upgrade():
    # Sessions with more than one hit are not bounces.
    op.execute(
        """
        UPDATE analytics_session
        SET is_bounce = false
        WHERE uuid IN (
            SELECT session_id
            FROM analytics_hit
            GROUP BY session_id
            HAVING COUNT(*) > 1
        )
        """
    )


def downgrade():
    pass

