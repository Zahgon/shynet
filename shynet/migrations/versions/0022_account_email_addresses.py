"""accounts: email address and confirmation tables

Ported from the account app's initial migrations

Revision ID: 0022_account_email_addresses
Revises: 0021_core_site
Create Date: 2022-06-24 11:44:00

"""
import sqlalchemy as sa
from alembic import op

from shynet.dbtypes import DateTimeUTC, big_integer

revision = "0022_account_email_addresses"
down_revision = "0021_core_site"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "account_emailaddress",
        sa.Column("id", big_integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", big_integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("primary", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["core_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="account_emailaddress_email_key"),
    )
    op.create_index(
        "ix_account_emailaddress_user_id", "account_emailaddress", ["user_id"]
    )
    op.create_table(
        "account_emailconfirmation",
        sa.Column("id", big_integer(), autoincrement=True, nullable=False),
        sa.Column("email_address_id", big_integer(), nullable=False),
        sa.Column("created", DateTimeUTC(), nullable=False),
        sa.Column("sent", DateTimeUTC(), nullable=True),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["email_address_id"], ["account_emailaddress.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="account_emailconfirmation_key_key"),
    )
    op.create_index(
        "ix_account_emailconfirmation_email_address_id",
        "account_emailconfirmation",
        ["email_address_id"],
    )


def downgrade():
    op.drop_table("account_emailconfirmation")
    op.drop_index("ix_account_emailaddress_user_id", table_name="account_emailaddress")
    op.drop_table("account_emailaddress")

