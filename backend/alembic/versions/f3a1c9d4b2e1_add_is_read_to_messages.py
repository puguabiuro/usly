"""add is_read to messages

Revision ID: f3a1c9d4b2e1
Revises: cc9328369424
Create Date: 2026-03-20 18:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3a1c9d4b2e1'
down_revision: Union[str, Sequence[str], None] = '91220d22ece5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_index('ix_messages_recipient_is_read', ['recipient_user_id', 'is_read'], unique=False)

    op.execute(
        sa.text(
            "UPDATE messages SET is_read = 1 WHERE sender_user_id IS NOT NULL"
        )
    )

    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.alter_column('is_read', server_default=None)


def downgrade() -> None:
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_index('ix_messages_recipient_is_read')
        batch_op.drop_column('is_read')
