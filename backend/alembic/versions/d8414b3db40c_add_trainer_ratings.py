"""add trainer ratings

Revision ID: d8414b3db40c
Revises: 658121b9fd5f
Create Date: 2026-09-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d8414b3db40c"
down_revision: Union[str, Sequence[str], None] = "658121b9fd5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trainer_ratings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("trainer_user_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("interest_tag", sa.String(length=120), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_trainer_ratings_rating_1_5",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["trainer_user_id"],
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
            name="uq_trainer_ratings_user_event",
        ),
    )

    op.create_index(
        op.f("ix_trainer_ratings_user_id"),
        "trainer_ratings",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_trainer_ratings_trainer_user_id"),
        "trainer_ratings",
        ["trainer_user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_trainer_ratings_event_id"),
        "trainer_ratings",
        ["event_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_trainer_ratings_interest_tag"),
        "trainer_ratings",
        ["interest_tag"],
        unique=False,
    )

    op.create_index(
        "ix_trainer_ratings_trainer_interest_created",
        "trainer_ratings",
        ["trainer_user_id", "interest_tag", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_trainer_ratings_trainer_interest_created",
        table_name="trainer_ratings",
    )
    op.drop_index(
        op.f("ix_trainer_ratings_interest_tag"),
        table_name="trainer_ratings",
    )
    op.drop_index(
        op.f("ix_trainer_ratings_event_id"),
        table_name="trainer_ratings",
    )
    op.drop_index(
        op.f("ix_trainer_ratings_trainer_user_id"),
        table_name="trainer_ratings",
    )
    op.drop_index(
        op.f("ix_trainer_ratings_user_id"),
        table_name="trainer_ratings",
    )
    op.drop_table("trainer_ratings")
