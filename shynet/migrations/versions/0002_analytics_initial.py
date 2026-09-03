"""analytics: initial

Ported from analytics/migrations/0001_initial.py

Revision ID: 0002_analytics_initial
Revises: 0001_core_initial
Create Date: 2020-04-14 14:40:00

"""
import sqlalchemy as sa
from alembic import op

from shynet.dbtypes import DateTimeUTC, GUID, IPAddress

revision = "0002_analytics_initial"
down_revision = "0001_core_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analytics_session",
        sa.Column("uuid", GUID(), nullable=False),
        sa.Column("service_id", GUID(), nullable=False),
        sa.Column("identifier", sa.Text(), nullable=False),
        sa.Column("start_time", DateTimeUTC(), nullable=False),
        sa.Column("last_seen", DateTimeUTC(), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=False),
        sa.Column("browser", sa.Text(), nullable=False),
        sa.Column("device", sa.Text(), nullable=False),
        sa.Column("device_type", sa.String(length=7), nullable=False),
        sa.Column("os", sa.Text(), nullable=False),
        sa.Column("ip", IPAddress(), nullable=False),
        sa.Column("asn", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("time_zone", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["service_id"], ["core_service.uuid"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_index(
        "ix_analytics_session_service_id", "analytics_session", ["service_id"]
    )
    op.create_index(
        "ix_analytics_session_identifier", "analytics_session", ["identifier"]
    )
    op.create_index(
        "ix_analytics_session_start_time", "analytics_session", ["start_time"]
    )
    op.create_index("ix_analytics_session_ip", "analytics_session", ["ip"])
    op.create_index(
        "analytics_session_service_start_time_idx",
        "analytics_session",
        ["service_id", sa.text("start_time DESC")],
    )
    op.create_index(
        "analytics_session_service_identifier_idx",
        "analytics_session",
        ["service_id", "identifier"],
    )

    op.create_table(
        "analytics_hit",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", GUID(), nullable=False),
        sa.Column("initial", sa.Boolean(), nullable=False),
        sa.Column("start_time", DateTimeUTC(), nullable=False),
        sa.Column("last_seen", DateTimeUTC(), nullable=False),
        sa.Column("heartbeats", sa.Integer(), nullable=False),
        sa.Column("tracker", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("referrer", sa.Text(), nullable=False),
        sa.Column("load_time", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"], ["analytics_session.uuid"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analytics_hit_session_id", "analytics_hit", ["session_id"])
    op.create_index("ix_analytics_hit_initial", "analytics_hit", ["initial"])
    op.create_index("ix_analytics_hit_start_time", "analytics_hit", ["start_time"])
    op.create_index("ix_analytics_hit_location", "analytics_hit", ["location"])
    op.create_index("ix_analytics_hit_referrer", "analytics_hit", ["referrer"])
    op.create_index(
        "analytics_hit_session_start_time_idx",
        "analytics_hit",
        ["session_id", sa.text("start_time DESC")],
    )
    op.create_index(
        "analytics_hit_session_location_idx", "analytics_hit", ["session_id", "location"]
    )
    op.create_index(
        "analytics_hit_session_referrer_idx", "analytics_hit", ["session_id", "referrer"]
    )


def downgrade():
    op.drop_table("analytics_hit")
    op.drop_table("analytics_session")
