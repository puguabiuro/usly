"""add social auth subjects to users

Revision ID: d1e7c4a9b620
Revises: 7c2a9f4e1d65
Create Date: 2026-07-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d1e7c4a9b620"
down_revision: Union[str, Sequence[str], None] = "7c2a9f4e1d65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("google_sub", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("apple_sub", sa.String(length=255), nullable=True),
    )

    op.create_index(
        "ix_users_google_sub",
        "users",
        ["google_sub"],
        unique=True,
    )
    op.create_index(
        "ix_users_apple_sub",
        "users",
        ["apple_sub"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_apple_sub", table_name="users")
    op.drop_index("ix_users_google_sub", table_name="users")

    op.drop_column("users", "apple_sub")
    op.drop_column("users", "google_sub")
