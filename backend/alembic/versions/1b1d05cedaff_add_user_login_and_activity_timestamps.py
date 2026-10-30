"""add user login and activity timestamps

Revision ID: 1b1d05cedaff
Revises: d8414b3db40c
Create Date: 2026-09-28 16:10:38.512951
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1b1d05cedaff"
down_revision: Union[str, Sequence[str], None] = "d8414b3db40c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "last_login_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "last_active_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )
        batch_op.create_index(
            batch_op.f("ix_users_last_login_at"),
            ["last_login_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_users_last_active_at"),
            ["last_active_at"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_last_active_at"))
        batch_op.drop_index(batch_op.f("ix_users_last_login_at"))
        batch_op.drop_column("last_active_at")
        batch_op.drop_column("last_login_at")
