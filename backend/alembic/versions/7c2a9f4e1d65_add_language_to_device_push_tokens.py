"""add language to device push tokens

Revision ID: 7c2a9f4e1d65
Revises: 4d8e6f1a2b73
Create Date: 2026-07-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "7c2a9f4e1d65"
down_revision: Union[str, Sequence[str], None] = "4d8e6f1a2b73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "device_push_tokens",
        sa.Column(
            "language",
            sa.String(length=5),
            nullable=False,
            server_default="pl",
        ),
    )
    op.create_index(
        "ix_device_push_tokens_language",
        "device_push_tokens",
        ["language"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_device_push_tokens_language",
        table_name="device_push_tokens",
    )
    op.drop_column("device_push_tokens", "language")
