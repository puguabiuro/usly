"""allow incomplete event drafts

Revision ID: b810f3f1e07a
Revises: 3e7a1c9d5b24
Create Date: 2026-09-15 18:24:17.598991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b810f3f1e07a'
down_revision: Union[str, Sequence[str], None] = '3e7a1c9d5b24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow incomplete data while an event is a draft."""
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.alter_column("title", existing_type=sa.String(length=120), nullable=True)
        batch_op.alter_column("city", existing_type=sa.String(length=80), nullable=True)
        batch_op.alter_column("where", existing_type=sa.String(length=120), nullable=True)
        batch_op.alter_column("interest_tag", existing_type=sa.String(length=40), nullable=True)
        batch_op.alter_column("start_at", existing_type=sa.DateTime(timezone=True), nullable=True)
        batch_op.alter_column("end_at", existing_type=sa.DateTime(timezone=True), nullable=True)


def downgrade() -> None:
    """Restore required event fields."""
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.alter_column("end_at", existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column("start_at", existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column("interest_tag", existing_type=sa.String(length=40), nullable=False)
        batch_op.alter_column("where", existing_type=sa.String(length=120), nullable=False)
        batch_op.alter_column("city", existing_type=sa.String(length=80), nullable=False)
        batch_op.alter_column("title", existing_type=sa.String(length=120), nullable=False)
