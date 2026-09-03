"""core: order services by name then uuid

Ported from core/migrations/0002_auto_20200415_1742.py

Revision ID: 0003_core_service_ordering
Revises: 0002_analytics_initial
Create Date: 2020-04-15 21:42:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0003_core_service_ordering"
down_revision = "0002_analytics_initial"
branch_labels = None
depends_on = None


def upgrade():
    # Ordering is declared on the model (`Service.default_order`); no schema change.
    pass


def downgrade():
    pass

