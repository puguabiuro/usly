"""add event location fields

Revision ID: 2c7f9a1d5b3e
Revises: 141d4e6c3253
Create Date: 2026-05-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2c7f9a1d5b3e"
down_revision: Union[str, Sequence[str], None] = "141d4e6c3253"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.add_column(sa.Column("address", sa.String(length=240), nullable=True))
        batch_op.add_column(sa.Column("location_lat", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("location_lng", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_column("location_lng")
        batch_op.drop_column("location_lat")
        batch_op.drop_column("address")
