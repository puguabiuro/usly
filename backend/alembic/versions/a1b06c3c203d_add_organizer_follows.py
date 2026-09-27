"""add organizer follows

Revision ID: a1b06c3c203d
Revises: d92a5b18d3b5
Create Date: 2026-09-20 19:14:25.993525
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b06c3c203d"
down_revision: Union[str, Sequence[str], None] = "d92a5b18d3b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizer_follows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("follower_user_id", sa.Integer(), nullable=False),
        sa.Column("organizer_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "follower_user_id <> organizer_user_id",
            name="ck_organizer_follows_no_self",
        ),
        sa.ForeignKeyConstraint(
            ["follower_user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organizer_user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "follower_user_id",
            "organizer_user_id",
            name="uq_organizer_follows_follower_organizer",
        ),
    )

    with op.batch_alter_table("organizer_follows", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_organizer_follows_created_at"),
            ["created_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_organizer_follows_follower_user_id"),
            ["follower_user_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_organizer_follows_organizer_created",
            ["organizer_user_id", "created_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_organizer_follows_organizer_user_id"),
            ["organizer_user_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("organizer_follows", schema=None) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_organizer_follows_organizer_user_id")
        )
        batch_op.drop_index(
            "ix_organizer_follows_organizer_created"
        )
        batch_op.drop_index(
            batch_op.f("ix_organizer_follows_follower_user_id")
        )
        batch_op.drop_index(
            batch_op.f("ix_organizer_follows_created_at")
        )

    op.drop_table("organizer_follows")
