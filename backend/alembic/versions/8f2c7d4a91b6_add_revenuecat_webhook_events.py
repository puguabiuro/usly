"""add RevenueCat webhook events

Revision ID: 8f2c7d4a91b6
Revises: 6c9f4a2e7b31
Create Date: 2026-07-11

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f2c7d4a91b6"
down_revision: Union[str, Sequence[str], None] = "6c9f4a2e7b31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the RevenueCat webhook event registry."""

    op.create_table(
        "revenuecat_webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=180), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("app_user_id", sa.String(length=180), nullable=True),
        sa.Column(
            "revenuecat_customer_id",
            sa.String(length=180),
            nullable=True,
        ),
        sa.Column("environment", sa.String(length=30), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "processing_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column(
            "last_retry_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_revenuecat_webhook_events_event_id"),
        "revenuecat_webhook_events",
        ["event_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_revenuecat_webhook_events_event_type"),
        "revenuecat_webhook_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenuecat_webhook_events_app_user_id"),
        "revenuecat_webhook_events",
        ["app_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenuecat_webhook_events_revenuecat_customer_id"),
        "revenuecat_webhook_events",
        ["revenuecat_customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenuecat_webhook_events_environment"),
        "revenuecat_webhook_events",
        ["environment"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenuecat_webhook_events_status"),
        "revenuecat_webhook_events",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenuecat_webhook_events_received_at"),
        "revenuecat_webhook_events",
        ["received_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenuecat_webhook_events_processed_at"),
        "revenuecat_webhook_events",
        ["processed_at"],
        unique=False,
    )
    op.create_index(
        "ix_revenuecat_webhook_events_status_received",
        "revenuecat_webhook_events",
        ["status", "received_at"],
        unique=False,
    )
    op.create_index(
        "ix_revenuecat_webhook_events_app_user_status",
        "revenuecat_webhook_events",
        ["app_user_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the RevenueCat webhook event registry."""

    op.drop_index(
        "ix_revenuecat_webhook_events_app_user_status",
        table_name="revenuecat_webhook_events",
    )
    op.drop_index(
        "ix_revenuecat_webhook_events_status_received",
        table_name="revenuecat_webhook_events",
    )
    op.drop_index(
        op.f("ix_revenuecat_webhook_events_processed_at"),
        table_name="revenuecat_webhook_events",
    )
    op.drop_index(
        op.f("ix_revenuecat_webhook_events_received_at"),
        table_name="revenuecat_webhook_events",
    )
    op.drop_index(
        op.f("ix_revenuecat_webhook_events_status"),
        table_name="revenuecat_webhook_events",
    )
    op.drop_index(
        op.f("ix_revenuecat_webhook_events_environment"),
        table_name="revenuecat_webhook_events",
    )
    op.drop_index(
        op.f(
            "ix_revenuecat_webhook_events_revenuecat_customer_id"
        ),
        table_name="revenuecat_webhook_events",
    )
    op.drop_index(
        op.f("ix_revenuecat_webhook_events_app_user_id"),
        table_name="revenuecat_webhook_events",
    )
    op.drop_index(
        op.f("ix_revenuecat_webhook_events_event_type"),
        table_name="revenuecat_webhook_events",
    )
    op.drop_index(
        op.f("ix_revenuecat_webhook_events_event_id"),
        table_name="revenuecat_webhook_events",
    )

    op.drop_table("revenuecat_webhook_events")
