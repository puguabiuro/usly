"""add private chat mutes

Revision ID: 4d8e6f1a2b73
Revises: 9b4e2c7d1a60
Create Date: 2026-07-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "4d8e6f1a2b73"
down_revision: Union[str, Sequence[str], None] = "9b4e2c7d1a60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "private_chat_mutes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("other_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("user_id <> other_user_id", name="ck_private_chat_mutes_no_self"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["other_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "other_user_id", name="uq_private_chat_mutes_user_other"),
    )
    op.create_index("ix_private_chat_mutes_user_id", "private_chat_mutes", ["user_id"])
    op.create_index("ix_private_chat_mutes_other_user_id", "private_chat_mutes", ["other_user_id"])
    op.create_index("ix_private_chat_mutes_created_at", "private_chat_mutes", ["created_at"])
    op.create_index(
        "ix_private_chat_mutes_user_created",
        "private_chat_mutes",
        ["user_id", "created_at"],
    )

    op.create_table(
        "group_mutes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "group_id", name="uq_group_mutes_user_group"),
    )
    op.create_index("ix_group_mutes_user_id", "group_mutes", ["user_id"])
    op.create_index("ix_group_mutes_group_id", "group_mutes", ["group_id"])
    op.create_index("ix_group_mutes_created_at", "group_mutes", ["created_at"])
    op.create_index(
        "ix_group_mutes_user_created",
        "group_mutes",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_group_mutes_user_created", table_name="group_mutes")
    op.drop_index("ix_group_mutes_created_at", table_name="group_mutes")
    op.drop_index("ix_group_mutes_group_id", table_name="group_mutes")
    op.drop_index("ix_group_mutes_user_id", table_name="group_mutes")
    op.drop_table("group_mutes")

    op.drop_index("ix_private_chat_mutes_user_created", table_name="private_chat_mutes")
    op.drop_index("ix_private_chat_mutes_created_at", table_name="private_chat_mutes")
    op.drop_index("ix_private_chat_mutes_other_user_id", table_name="private_chat_mutes")
    op.drop_index("ix_private_chat_mutes_user_id", table_name="private_chat_mutes")
    op.drop_table("private_chat_mutes")
