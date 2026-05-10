"""merge nearby radius and event location heads

Revision ID: 1b550d2a1be8
Revises: 9ab43fe0aed9, 2c7f9a1d5b3e
Create Date: 2026-05-10 11:45:05.640552

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b550d2a1be8'
down_revision: Union[str, Sequence[str], None] = ('9ab43fe0aed9', '2c7f9a1d5b3e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
