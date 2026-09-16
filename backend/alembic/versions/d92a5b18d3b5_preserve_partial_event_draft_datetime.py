"""preserve partial event draft datetime

Revision ID: d92a5b18d3b5
Revises: b810f3f1e07a
Create Date: 2026-09-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d92a5b18d3b5"
down_revision: Union[str, Sequence[str], None] = "b810f3f1e07a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Store partial date/time values while an event is still a draft."""
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.add_column(sa.Column("draft_date", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("draft_time", sa.Time(), nullable=True))


def downgrade() -> None:
    """Remove partial draft date/time storage."""
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_column("draft_time")
        batch_op.drop_column("draft_date")
