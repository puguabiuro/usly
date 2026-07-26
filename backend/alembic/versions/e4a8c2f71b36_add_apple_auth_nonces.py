"""add apple auth nonces

Revision ID: e4a8c2f71b36
Revises: d1e7c4a9b620
Create Date: 2026-07-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e4a8c2f71b36"
down_revision: Union[str, Sequence[str], None] = "d1e7c4a9b620"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "apple_auth_nonces",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nonce_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_apple_auth_nonces_nonce_hash",
        "apple_auth_nonces",
        ["nonce_hash"],
        unique=True,
    )
    op.create_index(
        "ix_apple_auth_nonces_expires_at",
        "apple_auth_nonces",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_apple_auth_nonces_used_at",
        "apple_auth_nonces",
        ["used_at"],
        unique=False,
    )
    op.create_index(
        "ix_apple_auth_nonces_created_at",
        "apple_auth_nonces",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_apple_auth_nonces_created_at",
        table_name="apple_auth_nonces",
    )
    op.drop_index(
        "ix_apple_auth_nonces_used_at",
        table_name="apple_auth_nonces",
    )
    op.drop_index(
        "ix_apple_auth_nonces_expires_at",
        table_name="apple_auth_nonces",
    )
    op.drop_index(
        "ix_apple_auth_nonces_nonce_hash",
        table_name="apple_auth_nonces",
    )

    op.drop_table("apple_auth_nonces")
