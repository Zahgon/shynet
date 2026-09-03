"""core: initial

Ported from core/migrations/0001_initial.py

Revision ID: 0001_core_initial
Revises:
Create Date: 2020-04-14 14:40:00

"""
import sqlalchemy as sa
from alembic import op

from shynet.dbtypes import DateTimeUTC, GUID

revision = "0001_core_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "core_user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("password", sa.String(length=128), nullable=False),
        sa.Column("last_login", DateTimeUTC(), nullable=True),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("first_name", sa.String(length=30), nullable=False),
        sa.Column("last_name", sa.String(length=150), nullable=False),
        sa.Column("is_staff", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("date_joined", DateTimeUTC(), nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="core_user_username_key"),
        sa.UniqueConstraint("email", name="core_user_email_key"),
    )
    op.create_table(
        "core_service",
        sa.Column("uuid", GUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created", DateTimeUTC(), nullable=False),
        sa.Column("link", sa.String(length=200), nullable=False),
        sa.Column("origins", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=2), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["core_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_index("ix_core_service_status", "core_service", ["status"])
    op.create_table(
        "core_service_collaborators",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_id", GUID(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["service_id"], ["core_service.uuid"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["core_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "service_id", "user_id", name="core_service_collaborators_uniq"
        ),
    )


def downgrade():
    op.drop_table("core_service_collaborators")
    op.drop_index("ix_core_service_status", table_name="core_service")
    op.drop_table("core_service")
    op.drop_table("core_user")
