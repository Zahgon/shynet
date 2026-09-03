"""core: add User.api_token and widen User.id

Ported from core/migrations/0009_auto_20211117_0217.py

Revision ID: 0018_core_user_api_token
Revises: 0017_analytics_update_bounce_stats
Create Date: 2021-11-17 07:17:00

"""
import sqlalchemy as sa
from alembic import op

from shynet.dbtypes import big_integer

revision = "0018_core_user_api_token"
down_revision = "0017_analytics_update_bounce_stats"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("core_user") as batch_op:
        batch_op.add_column(sa.Column("api_token", sa.Text(), nullable=True))
        batch_op.create_unique_constraint("core_user_api_token_key", ["api_token"])
        batch_op.alter_column(
            "id",
            existing_type=sa.Integer(),
            type_=big_integer(),
            existing_nullable=False,
            autoincrement=True,
        )
    with op.batch_alter_table("core_service") as batch_op:
        batch_op.alter_column(
            "owner_id",
            existing_type=sa.Integer(),
            type_=big_integer(),
            existing_nullable=False,
        )
    with op.batch_alter_table("core_service_collaborators") as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            type_=big_integer(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "id",
            existing_type=sa.Integer(),
            type_=big_integer(),
            existing_nullable=False,
            autoincrement=True,
        )


def downgrade():
    with op.batch_alter_table("core_service_collaborators") as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=big_integer(),
            type_=sa.Integer(),
            existing_nullable=False,
            autoincrement=True,
        )
        batch_op.alter_column(
            "user_id",
            existing_type=big_integer(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
    with op.batch_alter_table("core_service") as batch_op:
        batch_op.alter_column(
            "owner_id",
            existing_type=big_integer(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
    with op.batch_alter_table("core_user") as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=big_integer(),
            type_=sa.Integer(),
            existing_nullable=False,
            autoincrement=True,
        )
        batch_op.drop_constraint("core_user_api_token_key", type_="unique")
        batch_op.drop_column("api_token")
