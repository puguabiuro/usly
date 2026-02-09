"""init

Revision ID: cdc2685c1809
Revises:
Create Date: 2026-02-07 12:45:12.176724

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cdc2685c1809"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite-safe column alters using batch mode
    with op.batch_alter_table("events") as batch_op:
        batch_op.alter_column(
            "pricing_type",
            existing_type=sa.TEXT(),
            type_=sa.String(length=20),
            existing_nullable=False,
            existing_server_default=sa.text("'free'"),
        )
        batch_op.alter_column(
            "payment_link",
            existing_type=sa.TEXT(),
            type_=sa.String(length=500),
            existing_nullable=True,
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "terms_version",
            existing_type=sa.TEXT(),
            type_=sa.String(length=20),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "privacy_version",
            existing_type=sa.TEXT(),
            type_=sa.String(length=20),
            existing_nullable=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "privacy_version",
            existing_type=sa.String(length=20),
            type_=sa.TEXT(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "terms_version",
            existing_type=sa.String(length=20),
            type_=sa.TEXT(),
            existing_nullable=True,
        )

    with op.batch_alter_table("events") as batch_op:
        batch_op.alter_column(
            "payment_link",
            existing_type=sa.String(length=500),
            type_=sa.TEXT(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "pricing_type",
            existing_type=sa.String(length=20),
            type_=sa.TEXT(),
            existing_nullable=False,
            existing_server_default=sa.text("'free'"),
        )
