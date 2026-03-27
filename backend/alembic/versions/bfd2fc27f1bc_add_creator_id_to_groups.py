"""add creator_id_to_groups

Revision ID: bfd2fc27f1bc
Revises: 8a7747c2a3f4
Create Date: 2026-03-14 18:44:09.781728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfd2fc27f1bc'
down_revision: Union[str, Sequence[str], None] = '8a7747c2a3f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "groups",
        sa.Column("creator_id", sa.Integer(), nullable=True),
    )
    with op.batch_alter_table("groups", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_groups_creator_id"), ["creator_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_groups_creator_id_users",
            "users",
            ["creator_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("groups", schema=None) as batch_op:
        batch_op.drop_constraint("fk_groups_creator_id_users", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_groups_creator_id"))
    op.drop_column("groups", "creator_id")
