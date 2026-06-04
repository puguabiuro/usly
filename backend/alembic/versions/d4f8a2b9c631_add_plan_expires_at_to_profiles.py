"""add plan expires at to profiles

Revision ID: d4f8a2b9c631
Revises: c06796ada409
Create Date: 2026-06-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4f8a2b9c631"
down_revision: Union[str, Sequence[str], None] = "c06796ada409"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("partner_profiles", sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("partner_profiles", "plan_expires_at")
    op.drop_column("user_profiles", "plan_expires_at")
