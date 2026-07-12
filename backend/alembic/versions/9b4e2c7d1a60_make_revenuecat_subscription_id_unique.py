"""make RevenueCat subscription ID unique

Revision ID: 9b4e2c7d1a60
Revises: 3a7d9c5e1f42
Create Date: 2026-07-12

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9b4e2c7d1a60"
down_revision: Union[str, Sequence[str], None] = "3a7d9c5e1f42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEX_NAME = "ix_store_purchases_revenuecat_subscription_id"


def upgrade() -> None:
    """Replace the ordinary RevenueCat subscription index with a unique one."""

    op.drop_index(
        INDEX_NAME,
        table_name="store_purchases",
    )
    op.create_index(
        INDEX_NAME,
        "store_purchases",
        ["revenuecat_subscription_id"],
        unique=True,
    )


def downgrade() -> None:
    """Restore the ordinary non-unique RevenueCat subscription index."""

    op.drop_index(
        INDEX_NAME,
        table_name="store_purchases",
    )
    op.create_index(
        INDEX_NAME,
        "store_purchases",
        ["revenuecat_subscription_id"],
        unique=False,
    )
