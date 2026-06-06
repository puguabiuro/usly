"""add plan expiry notice fields

Revision ID: b7e2c4d9a105
Revises: a6f4c2d9e801
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa


revision = "b7e2c4d9a105"
down_revision = "a6f4c2d9e801"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("plan_expiry_notice_14d_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_profiles", sa.Column("plan_expiry_notice_7d_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("partner_profiles", sa.Column("plan_expiry_notice_14d_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("partner_profiles", sa.Column("plan_expiry_notice_7d_sent_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("partner_profiles", "plan_expiry_notice_7d_sent_at")
    op.drop_column("partner_profiles", "plan_expiry_notice_14d_sent_at")
    op.drop_column("user_profiles", "plan_expiry_notice_7d_sent_at")
    op.drop_column("user_profiles", "plan_expiry_notice_14d_sent_at")
