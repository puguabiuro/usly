"""add ai usage logs

Revision ID: df9f4dbd60bf
Revises: 1b550d2a1be8
Create Date: 2026-05-14 21:04:00.365126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df9f4dbd60bf'
down_revision: Union[str, Sequence[str], None] = '1b550d2a1be8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ai_usage_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("feature", sa.String(length=50), nullable=False),
        sa.Column("plan", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_usage_logs_user_id"), "ai_usage_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_ai_usage_logs_feature"), "ai_usage_logs", ["feature"], unique=False)
    op.create_index(op.f("ix_ai_usage_logs_created_at"), "ai_usage_logs", ["created_at"], unique=False)
    op.create_index(
        "ix_ai_usage_user_feature_created",
        "ai_usage_logs",
        ["user_id", "feature", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_ai_usage_user_feature_created", table_name="ai_usage_logs")
    op.drop_index(op.f("ix_ai_usage_logs_created_at"), table_name="ai_usage_logs")
    op.drop_index(op.f("ix_ai_usage_logs_feature"), table_name="ai_usage_logs")
    op.drop_index(op.f("ix_ai_usage_logs_user_id"), table_name="ai_usage_logs")
    op.drop_table("ai_usage_logs")
