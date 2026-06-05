"""add ambassador reward grants

Revision ID: f1b7c9a2d441
Revises: e8b1a6c4d902
Create Date: 2026-06-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1b7c9a2d441"
down_revision: Union[str, Sequence[str], None] = "e8b1a6c4d902"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ambassador_reward_grants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("ambassador_user_id", sa.Integer(), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.Column("reward_number", sa.Integer(), nullable=False),
        sa.Column("reward_months", sa.Integer(), nullable=False),
        sa.Column("paid_activations_count", sa.Integer(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("plan_expires_at_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("plan_expires_at_after", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["campaign_id"], ["promo_campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ambassador_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("campaign_id", "reward_number", name="uq_ambassador_reward_campaign_number"),
    )

    op.create_index(
        "ix_ambassador_rewards_user_campaign",
        "ambassador_reward_grants",
        ["ambassador_user_id", "campaign_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ambassador_rewards_user_campaign", table_name="ambassador_reward_grants")
    op.drop_table("ambassador_reward_grants")
