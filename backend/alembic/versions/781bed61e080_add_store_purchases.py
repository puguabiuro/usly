"""add store purchases

Revision ID: 781bed61e080
Revises: b7e2c4d9a105
Create Date: 2026-06-10 21:07:03.704468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '781bed61e080'
down_revision: Union[str, Sequence[str], None] = 'b7e2c4d9a105'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "store_purchases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("product_id", sa.String(length=160), nullable=False),
        sa.Column("transaction_id", sa.String(length=180), nullable=False),
        sa.Column("plan", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("verification_mode", sa.String(length=30), nullable=False),
        sa.Column("raw_payload", sa.Text(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("platform", "transaction_id", name="uq_store_purchases_platform_transaction"),
    )
    op.create_index(op.f("ix_store_purchases_platform"), "store_purchases", ["platform"], unique=False)
    op.create_index(op.f("ix_store_purchases_status"), "store_purchases", ["status"], unique=False)
    op.create_index(op.f("ix_store_purchases_verified_at"), "store_purchases", ["verified_at"], unique=False)
    op.create_index("ix_store_purchases_user_status", "store_purchases", ["user_id", "status"], unique=False)
    op.create_index(op.f("ix_store_purchases_user_id"), "store_purchases", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_store_purchases_user_id"), table_name="store_purchases")
    op.drop_index("ix_store_purchases_user_status", table_name="store_purchases")
    op.drop_index(op.f("ix_store_purchases_verified_at"), table_name="store_purchases")
    op.drop_index(op.f("ix_store_purchases_status"), table_name="store_purchases")
    op.drop_index(op.f("ix_store_purchases_platform"), table_name="store_purchases")
    op.drop_table("store_purchases")
