"""add apple auth credentials

Revision ID: f7b1d3a84c62
Revises: e4a8c2f71b36
Create Date: 2026-07-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f7b1d3a84c62"
down_revision: Union[str, Sequence[str], None] = "e4a8c2f71b36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "apple_auth_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.String(length=255), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "client_id",
            name="uq_apple_auth_credentials_user_client",
        ),
    )

    op.create_index(
        "ix_apple_auth_credentials_user_id",
        "apple_auth_credentials",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_apple_auth_credentials_client_id",
        "apple_auth_credentials",
        ["client_id"],
        unique=False,
    )
    op.create_index(
        "ix_apple_auth_credentials_revoked_at",
        "apple_auth_credentials",
        ["revoked_at"],
        unique=False,
    )
    op.create_index(
        "ix_apple_auth_credentials_created_at",
        "apple_auth_credentials",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_apple_auth_credentials_updated_at",
        "apple_auth_credentials",
        ["updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_apple_auth_credentials_updated_at",
        table_name="apple_auth_credentials",
    )
    op.drop_index(
        "ix_apple_auth_credentials_created_at",
        table_name="apple_auth_credentials",
    )
    op.drop_index(
        "ix_apple_auth_credentials_revoked_at",
        table_name="apple_auth_credentials",
    )
    op.drop_index(
        "ix_apple_auth_credentials_client_id",
        table_name="apple_auth_credentials",
    )
    op.drop_index(
        "ix_apple_auth_credentials_user_id",
        table_name="apple_auth_credentials",
    )

    op.drop_table("apple_auth_credentials")
