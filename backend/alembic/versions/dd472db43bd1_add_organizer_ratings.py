"""add organizer ratings

Revision ID: dd472db43bd1
Revises: a1b06c3c203d
Create Date: 2026-09-21 12:26:37.606833
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "dd472db43bd1"
down_revision: Union[str, Sequence[str], None] = "a1b06c3c203d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizer_ratings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("organizer_user_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_organizer_ratings_rating_1_5",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organizer_user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "event_id",
            name="uq_organizer_ratings_user_event",
        ),
    )

    with op.batch_alter_table("organizer_ratings", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_organizer_ratings_event_id"),
            ["event_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_organizer_ratings_organizer_created",
            ["organizer_user_id", "created_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_organizer_ratings_organizer_user_id"),
            ["organizer_user_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_organizer_ratings_user_id"),
            ["user_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("organizer_ratings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_organizer_ratings_user_id"))
        batch_op.drop_index(batch_op.f("ix_organizer_ratings_organizer_user_id"))
        batch_op.drop_index("ix_organizer_ratings_organizer_created")
        batch_op.drop_index(batch_op.f("ix_organizer_ratings_event_id"))

    op.drop_table("organizer_ratings")
