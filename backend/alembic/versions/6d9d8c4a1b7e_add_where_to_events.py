"""add where to events

Revision ID: 6d9d8c4a1b7e
Revises: f3a1c9d4b2e1
Create Date: 2026-03-20 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6d9d8c4a1b7e'
down_revision: Union[str, Sequence[str], None] = 'f3a1c9d4b2e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('where', sa.String(length=120), nullable=False, server_default=''))

    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.alter_column('where', server_default=None)


def downgrade() -> None:
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_column('where')
