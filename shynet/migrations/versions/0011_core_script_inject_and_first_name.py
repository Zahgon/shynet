"""core: add Service.script_inject and widen User.first_name

Ported from core/migrations/0008_auto_20200628_1403.py

Revision ID: 0011_core_script_inject_and_first_name
Revises: 0010_core_service_ignore_robots
Create Date: 2020-06-28 18:03:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0011_core_script_inject_and_first_name"
down_revision = "0010_core_service_ignore_robots"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "core_service",
        sa.Column("script_inject", sa.Text(), nullable=False, server_default=""),
    )
    with op.batch_alter_table("core_service") as batch_op:
        batch_op.alter_column(
            "script_inject",
            existing_type=sa.Text(),
            existing_nullable=False,
            server_default=None,
        )
    with op.batch_alter_table("core_user") as batch_op:
        batch_op.alter_column(
            "first_name",
            existing_type=sa.String(length=30),
            type_=sa.String(length=150),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table("core_user") as batch_op:
        batch_op.alter_column(
            "first_name",
            existing_type=sa.String(length=150),
            type_=sa.String(length=30),
            existing_nullable=False,
        )
    op.drop_column("core_service", "script_inject")

