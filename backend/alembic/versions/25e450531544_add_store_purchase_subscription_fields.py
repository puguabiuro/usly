"""add store purchase subscription fields

Revision ID: 25e450531544
Revises: 781bed61e080
Create Date: 2026-06-12 18:19:46.240063

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25e450531544'
down_revision: Union[str, Sequence[str], None] = '781bed61e080'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("store_purchases", sa.Column("original_transaction_id", sa.String(length=180), nullable=True))
    op.add_column("store_purchases", sa.Column("purchase_token", sa.String(length=260), nullable=True))
    op.add_column("store_purchases", sa.Column("environment", sa.String(length=30), nullable=True))
    op.add_column("store_purchases", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("store_purchases", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_store_purchases_original_transaction_id"), "store_purchases", ["original_transaction_id"], unique=False)
    op.create_index(op.f("ix_store_purchases_purchase_token"), "store_purchases", ["purchase_token"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_store_purchases_purchase_token"), table_name="store_purchases")
    op.drop_index(op.f("ix_store_purchases_original_transaction_id"), table_name="store_purchases")
    op.drop_column("store_purchases", "revoked_at")
    op.drop_column("store_purchases", "expires_at")
    op.drop_column("store_purchases", "environment")
    op.drop_column("store_purchases", "purchase_token")
    op.drop_column("store_purchases", "original_transaction_id")
