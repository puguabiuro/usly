"""add RevenueCat identity to users

Revision ID: 3a7d9c5e1f42
Revises: 8f2c7d4a91b6
Create Date: 2026-07-12

"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3a7d9c5e1f42"
down_revision: Union[str, Sequence[str], None] = "8f2c7d4a91b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


REVENUECAT_APP_USER_ID_PREFIX = "usly_usr_"
REVENUECAT_APP_USER_ID_INDEX = (
    "ix_users_revenuecat_app_user_id"
)


def _generate_revenuecat_app_user_id() -> str:
    """Generate a migration-safe RevenueCat App User ID."""

    return f"{REVENUECAT_APP_USER_ID_PREFIX}{uuid4().hex}"


def upgrade() -> None:
    """Add and backfill stable RevenueCat identities for all users."""

    op.add_column(
        "users",
        sa.Column(
            "revenuecat_app_user_id",
            sa.String(length=64),
            nullable=True,
        ),
    )

    connection = op.get_bind()

    user_ids = [
        row[0]
        for row in connection.execute(
            sa.text("SELECT id FROM users ORDER BY id")
        ).fetchall()
    ]

    generated_identifiers: set[str] = set()

    for user_id in user_ids:
        app_user_id = _generate_revenuecat_app_user_id()

        while app_user_id in generated_identifiers:
            app_user_id = _generate_revenuecat_app_user_id()

        generated_identifiers.add(app_user_id)

        connection.execute(
            sa.text(
                """
                UPDATE users
                SET revenuecat_app_user_id = :app_user_id
                WHERE id = :user_id
                """
            ),
            {
                "app_user_id": app_user_id,
                "user_id": user_id,
            },
        )

    null_count = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM users
            WHERE revenuecat_app_user_id IS NULL
               OR TRIM(revenuecat_app_user_id) = ''
            """
        )
    ).scalar_one()

    duplicate_count = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM (
                SELECT revenuecat_app_user_id
                FROM users
                GROUP BY revenuecat_app_user_id
                HAVING COUNT(*) > 1
            ) AS duplicated_revenuecat_ids
            """
        )
    ).scalar_one()

    if null_count != 0:
        raise RuntimeError(
            "RevenueCat identity backfill pozostawił puste identyfikatory"
        )

    if duplicate_count != 0:
        raise RuntimeError(
            "RevenueCat identity backfill utworzył duplikaty"
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "revenuecat_app_user_id",
            existing_type=sa.String(length=64),
            nullable=False,
        )

    op.create_index(
        REVENUECAT_APP_USER_ID_INDEX,
        "users",
        ["revenuecat_app_user_id"],
        unique=True,
    )


def downgrade() -> None:
    """Remove RevenueCat identities from users."""

    op.drop_index(
        REVENUECAT_APP_USER_ID_INDEX,
        table_name="users",
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("revenuecat_app_user_id")
