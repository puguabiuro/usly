"""Add ownership proof hash to device push tokens.

Revision ID: a6f2c8d4e901
Revises: 9e4a2c7b1d30
"""

from alembic import op
import sqlalchemy as sa

revision = "a6f2c8d4e901"
down_revision = "9e4a2c7b1d30"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "device_push_tokens",
        sa.Column("ownership_proof_hash", sa.String(length=64), nullable=True),
    )


def downgrade():
    op.drop_column("device_push_tokens", "ownership_proof_hash")
