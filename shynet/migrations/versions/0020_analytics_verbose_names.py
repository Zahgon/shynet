"""analytics: widen Hit.id and add translated field names

Ported from analytics/migrations/0010_auto_20220624_0744.py

Revision ID: 0020_analytics_verbose_names
Revises: 0019_core_service_verbose_names
Create Date: 2022-06-24 11:44:00

"""
import sqlalchemy as sa
from alembic import op

from shynet.dbtypes import big_integer

revision = "0020_analytics_verbose_names"
down_revision = "0019_core_service_verbose_names"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("analytics_hit") as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=sa.Integer(),
            type_=big_integer(),
            existing_nullable=False,
            autoincrement=True,
        )
    # The remaining changes are verbose names, which live on the model.


def downgrade():
    with op.batch_alter_table("analytics_hit") as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=big_integer(),
            type_=sa.Integer(),
            existing_nullable=False,
            autoincrement=True,
        )

