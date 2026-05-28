"""add trainer interests to user profiles

Revision ID: 20260528_trainer_interests
Revises: 485cc3af9324
Create Date: 2026-05-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260528_trainer_interests"
down_revision: Union[str, None] = "485cc3af9324"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("trainer_interests_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_profiles", "trainer_interests_json")
