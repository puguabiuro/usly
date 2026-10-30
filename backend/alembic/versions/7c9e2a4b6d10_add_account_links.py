"""add linked companion and organizer accounts

Revision ID: 7c9e2a4b6d10
Revises: 1b1d05cedaff
Create Date: 2026-10-27
"""

from alembic import op
import sqlalchemy as sa

revision = "7c9e2a4b6d10"
down_revision = "1b1d05cedaff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "account_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["partner_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_account_links_user_id"),
        sa.UniqueConstraint("partner_id", name="uq_account_links_partner_id"),
        sa.CheckConstraint(
            "user_id <> partner_id",
            name="ck_account_links_distinct_users",
        ),
    )


def downgrade() -> None:
    op.drop_table("account_links")
