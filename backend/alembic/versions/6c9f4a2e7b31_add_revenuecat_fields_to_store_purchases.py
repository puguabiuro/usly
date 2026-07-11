"""add RevenueCat fields to store purchases

Revision ID: 6c9f4a2e7b31
Revises: 428f2b6dc985
Create Date: 2026-07-11

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6c9f4a2e7b31"
down_revision: Union[str, Sequence[str], None] = "428f2b6dc985"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add RevenueCat synchronization fields."""

    op.add_column(
        "store_purchases",
        sa.Column(
            "revenuecat_app_user_id",
            sa.String(length=180),
            nullable=True,
        ),
    )
    op.add_column(
        "store_purchases",
        sa.Column(
            "revenuecat_customer_id",
            sa.String(length=180),
            nullable=True,
        ),
    )
    op.add_column(
        "store_purchases",
        sa.Column(
            "revenuecat_subscription_id",
            sa.String(length=180),
            nullable=True,
        ),
    )
    op.add_column(
        "store_purchases",
        sa.Column(
            "revenuecat_entitlement_id",
            sa.String(length=180),
            nullable=True,
        ),
    )
    op.add_column(
        "store_purchases",
        sa.Column(
            "entitlement_lookup_key",
            sa.String(length=160),
            nullable=True,
        ),
    )
    op.add_column(
        "store_purchases",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=True,
        ),
    )
    op.add_column(
        "store_purchases",
        sa.Column(
            "store",
            sa.String(length=30),
            nullable=True,
        ),
    )
    op.add_column(
        "store_purchases",
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "store_purchases",
        sa.Column(
            "last_event_id",
            sa.String(length=180),
            nullable=True,
        ),
    )
    op.add_column(
        "store_purchases",
        sa.Column(
            "last_event_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_store_purchases_revenuecat_app_user_id"),
        "store_purchases",
        ["revenuecat_app_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_store_purchases_revenuecat_customer_id"),
        "store_purchases",
        ["revenuecat_customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_store_purchases_revenuecat_subscription_id"),
        "store_purchases",
        ["revenuecat_subscription_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_store_purchases_revenuecat_entitlement_id"),
        "store_purchases",
        ["revenuecat_entitlement_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_store_purchases_entitlement_lookup_key"),
        "store_purchases",
        ["entitlement_lookup_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_store_purchases_role"),
        "store_purchases",
        ["role"],
        unique=False,
    )
    op.create_index(
        op.f("ix_store_purchases_store"),
        "store_purchases",
        ["store"],
        unique=False,
    )
    op.create_index(
        op.f("ix_store_purchases_synced_at"),
        "store_purchases",
        ["synced_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_store_purchases_last_event_id"),
        "store_purchases",
        ["last_event_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove RevenueCat synchronization fields."""

    op.drop_index(
        op.f("ix_store_purchases_last_event_id"),
        table_name="store_purchases",
    )
    op.drop_index(
        op.f("ix_store_purchases_synced_at"),
        table_name="store_purchases",
    )
    op.drop_index(
        op.f("ix_store_purchases_store"),
        table_name="store_purchases",
    )
    op.drop_index(
        op.f("ix_store_purchases_role"),
        table_name="store_purchases",
    )
    op.drop_index(
        op.f("ix_store_purchases_entitlement_lookup_key"),
        table_name="store_purchases",
    )
    op.drop_index(
        op.f("ix_store_purchases_revenuecat_entitlement_id"),
        table_name="store_purchases",
    )
    op.drop_index(
        op.f("ix_store_purchases_revenuecat_subscription_id"),
        table_name="store_purchases",
    )
    op.drop_index(
        op.f("ix_store_purchases_revenuecat_customer_id"),
        table_name="store_purchases",
    )
    op.drop_index(
        op.f("ix_store_purchases_revenuecat_app_user_id"),
        table_name="store_purchases",
    )

    op.drop_column("store_purchases", "last_event_at")
    op.drop_column("store_purchases", "last_event_id")
    op.drop_column("store_purchases", "synced_at")
    op.drop_column("store_purchases", "store")
    op.drop_column("store_purchases", "role")
    op.drop_column("store_purchases", "entitlement_lookup_key")
    op.drop_column("store_purchases", "revenuecat_entitlement_id")
    op.drop_column("store_purchases", "revenuecat_subscription_id")
    op.drop_column("store_purchases", "revenuecat_customer_id")
    op.drop_column("store_purchases", "revenuecat_app_user_id")
