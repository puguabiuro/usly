"""add group memberships

Revision ID: 8a7747c2a3f4
Revises: 82e72aa9e314
Create Date: 2026-03-14 17:17:18.315538

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a7747c2a3f4'
down_revision: Union[str, Sequence[str], None] = '82e72aa9e314'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "group_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "group_id", name="uq_group_memberships_user_group"),
    )
    with op.batch_alter_table("group_memberships", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_group_memberships_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_group_memberships_group_id"), ["group_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("group_memberships", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_group_memberships_group_id"))
        batch_op.drop_index(batch_op.f("ix_group_memberships_user_id"))
    op.drop_table("group_memberships")
