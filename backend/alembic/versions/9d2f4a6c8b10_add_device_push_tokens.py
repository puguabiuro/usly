"""add device push tokens

Revision ID: 9d2f4a6c8b10
Revises: 25e450531544
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa


revision = "9d2f4a6c8b10"
down_revision = "25e450531544"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "device_push_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("device_id", sa.String(length=120), nullable=True),
        sa.Column("app_version", sa.String(length=40), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_device_push_tokens_token"),
    )
    op.create_index("ix_device_push_tokens_user_id", "device_push_tokens", ["user_id"])
    op.create_index("ix_device_push_tokens_token", "device_push_tokens", ["token"])
    op.create_index("ix_device_push_tokens_platform", "device_push_tokens", ["platform"])
    op.create_index("ix_device_push_tokens_is_active", "device_push_tokens", ["is_active"])
    op.create_index("ix_device_push_tokens_created_at", "device_push_tokens", ["created_at"])
    op.create_index("ix_device_push_tokens_last_seen_at", "device_push_tokens", ["last_seen_at"])
    op.create_index("ix_device_push_tokens_user_active", "device_push_tokens", ["user_id", "is_active"])
    op.create_index("ix_device_push_tokens_platform_active", "device_push_tokens", ["platform", "is_active"])


def downgrade():
    op.drop_index("ix_device_push_tokens_platform_active", table_name="device_push_tokens")
    op.drop_index("ix_device_push_tokens_user_active", table_name="device_push_tokens")
    op.drop_index("ix_device_push_tokens_last_seen_at", table_name="device_push_tokens")
    op.drop_index("ix_device_push_tokens_created_at", table_name="device_push_tokens")
    op.drop_index("ix_device_push_tokens_is_active", table_name="device_push_tokens")
    op.drop_index("ix_device_push_tokens_platform", table_name="device_push_tokens")
    op.drop_index("ix_device_push_tokens_token", table_name="device_push_tokens")
    op.drop_index("ix_device_push_tokens_user_id", table_name="device_push_tokens")
    op.drop_table("device_push_tokens")
