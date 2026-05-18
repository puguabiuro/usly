"""add email verification

Revision ID: 20260518_email_verification
Revises: df9f4dbd60bf
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa


revision = "20260518_email_verification"
down_revision = "df9f4dbd60bf"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_users_email_verified_at",
        "users",
        ["email_verified_at"],
        unique=False,
    )

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_email_verification_tokens_user_id", "email_verification_tokens", ["user_id"], unique=False)
    op.create_index("ix_email_verification_tokens_token", "email_verification_tokens", ["token"], unique=True)
    op.create_index("ix_email_verification_tokens_expires_at", "email_verification_tokens", ["expires_at"], unique=False)
    op.create_index("ix_email_verification_tokens_used_at", "email_verification_tokens", ["used_at"], unique=False)
    op.create_index(
        "ix_email_verification_tokens_user_used",
        "email_verification_tokens",
        ["user_id", "used_at"],
        unique=False,
    )
    op.create_index("ix_email_verification_tokens_created_at", "email_verification_tokens", ["created_at"], unique=False)


def downgrade():
    op.drop_index("ix_email_verification_tokens_created_at", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_user_used", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_used_at", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_expires_at", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_token", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_user_id", table_name="email_verification_tokens")
    op.drop_table("email_verification_tokens")

    op.drop_index("ix_users_email_verified_at", table_name="users")
    op.drop_column("users", "email_verified_at")
