"""align events interest_tag schema

Revision ID: 141d4e6c3253
Revises: 1f534ab4a54f
Create Date: 2026-04-22 19:47:49.237249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '141d4e6c3253'
down_revision: Union[str, Sequence[str], None] = '1f534ab4a54f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col.get("name") == column_name for col in inspector.get_columns(table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(ix.get("name") == index_name for ix in inspector.get_indexes(table_name))


def upgrade() -> None:
    """Upgrade schema."""

    if not _column_exists("events", "interest_tag"):
        with op.batch_alter_table("events", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "interest_tag",
                    sa.String(length=40),
                    nullable=False,
                    server_default=sa.text("'eventy'"),
                )
            )
    else:
        with op.batch_alter_table("events", schema=None) as batch_op:
            batch_op.alter_column(
                "interest_tag",
                existing_type=sa.TEXT(),
                type_=sa.String(length=40),
                existing_nullable=False,
                existing_server_default=sa.text("'eventy'"),
            )

    if not _index_exists("events", "ix_events_interest_tag"):
        with op.batch_alter_table("events", schema=None) as batch_op:
            batch_op.create_index(
                batch_op.f("ix_events_interest_tag"),
                ["interest_tag"],
                unique=False,
            )


def downgrade() -> None:
    """Downgrade schema."""

    if _index_exists("events", "ix_events_interest_tag"):
        with op.batch_alter_table("events", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_events_interest_tag"))

    if _column_exists("events", "interest_tag"):
        with op.batch_alter_table("events", schema=None) as batch_op:
            batch_op.alter_column(
                "interest_tag",
                existing_type=sa.String(length=40),
                type_=sa.TEXT(),
                existing_nullable=False,
                existing_server_default=sa.text("'eventy'"),
            )
