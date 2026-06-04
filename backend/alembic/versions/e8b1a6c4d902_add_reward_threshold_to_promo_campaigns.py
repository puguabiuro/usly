"""add reward threshold to promo campaigns

Revision ID: e8b1a6c4d902
Revises: d4f8a2b9c631
Create Date: 2026-06-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8b1a6c4d902"
down_revision: Union[str, Sequence[str], None] = "d4f8a2b9c631"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("promo_campaigns", sa.Column("reward_threshold", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("promo_campaigns", "reward_threshold")
