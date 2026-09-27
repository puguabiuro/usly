"""add event type for trainer events

Revision ID: 658121b9fd5f
Revises: dd472db43bd1
Create Date: 2026-09-26 13:55:29.144501

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '658121b9fd5f'
down_revision: Union[str, Sequence[str], None] = 'dd472db43bd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add event type while preserving all existing events as organizer events."""
    op.add_column(
        "events",
        sa.Column(
            "event_type",
            sa.String(length=20),
            nullable=False,
            server_default="organizer",
        ),
    )
    op.create_index(
        "ix_events_event_type",
        "events",
        ["event_type"],
        unique=False,
    )


def downgrade() -> None:
    """Remove event type."""
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_column("events", "event_type")
