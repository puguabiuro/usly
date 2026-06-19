"""add admin mfa fields

Revision ID: 428f2b6dc985
Revises: 85bcb0b31b8d
Create Date: 2026-06-19 17:28:54.154522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '428f2b6dc985'
down_revision: Union[str, Sequence[str], None] = '85bcb0b31b8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('mfa_secret', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('mfa_backup_codes_hash', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('mfa_enabled_at', sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('mfa_enabled_at')
        batch_op.drop_column('mfa_backup_codes_hash')
        batch_op.drop_column('mfa_secret')
        batch_op.drop_column('mfa_enabled')
