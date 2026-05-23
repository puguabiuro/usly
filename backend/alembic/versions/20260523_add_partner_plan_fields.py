"""add partner plan fields

Revision ID: 20260523_partner_plan_fields
Revises: 20260518_email_verification
Create Date: 2026-05-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260523_partner_plan_fields"
down_revision: Union[str, Sequence[str], None] = "20260518_email_verification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col.get("name") == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _column_exists("partner_profiles", "plan_source"):
        op.add_column("partner_profiles", sa.Column("plan_source", sa.String(length=20), nullable=True))
    if not _column_exists("partner_profiles", "plan_status"):
        op.add_column("partner_profiles", sa.Column("plan_status", sa.String(length=20), nullable=True))
    if not _column_exists("partner_profiles", "plan_updated_at"):
        op.add_column("partner_profiles", sa.Column("plan_updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    if _column_exists("partner_profiles", "plan_updated_at"):
        op.drop_column("partner_profiles", "plan_updated_at")
    if _column_exists("partner_profiles", "plan_status"):
        op.drop_column("partner_profiles", "plan_status")
    if _column_exists("partner_profiles", "plan_source"):
        op.drop_column("partner_profiles", "plan_source")
