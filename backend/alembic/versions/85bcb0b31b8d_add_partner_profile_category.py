"""add partner profile category

Revision ID: 85bcb0b31b8d
Revises: 9d2f4a6c8b10
Create Date: 2026-06-18 18:22:24.772590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '85bcb0b31b8d'
down_revision: Union[str, Sequence[str], None] = '9d2f4a6c8b10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    if not _has_column("partner_profiles", "kategoria"):
        op.add_column("partner_profiles", sa.Column("kategoria", sa.String(length=80), nullable=True))
    if not _has_column("partner_profiles", "plan"):
        op.add_column("partner_profiles", sa.Column("plan", sa.String(length=20), nullable=False, server_default="free"))


def downgrade() -> None:
    """Downgrade schema."""
    if _has_column("partner_profiles", "plan"):
        op.drop_column("partner_profiles", "plan")
    if _has_column("partner_profiles", "kategoria"):
        op.drop_column("partner_profiles", "kategoria")
