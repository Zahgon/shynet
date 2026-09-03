"""core: translated field names for Service

Ported from core/migrations/0010_auto_20220624_0744.py

Revision ID: 0019_core_service_verbose_names
Revises: 0018_core_user_api_token
Create Date: 2022-06-24 11:44:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0019_core_service_verbose_names"
down_revision = "0018_core_user_api_token"
branch_labels = None
depends_on = None


def upgrade():
    # Verbose names live on the model (`info={"verbose_name": ...}`); no schema change.
    pass


def downgrade():
    pass

