"""add user plan fields

Revision ID: 82e72aa9e314
Revises: c4cb54b6e244
Create Date: 2026-03-14 17:00:10.000340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82e72aa9e314'
down_revision: Union[str, Sequence[str], None] = 'c4cb54b6e244'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "user_profiles",
        sa.Column("plan", sa.String(length=20), nullable=False, server_default="free"),
    )
    op.add_column(
        "user_profiles",
        sa.Column("plan_source", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "user_profiles",
        sa.Column("plan_status", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "user_profiles",
        sa.Column("plan_updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("user_profiles", "plan_updated_at")
    op.drop_column("user_profiles", "plan_status")
    op.drop_column("user_profiles", "plan_source")
    op.drop_column("user_profiles", "plan")
