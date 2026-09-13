"""add group interest tags json

Revision ID: 3e7a1c9d5b24
Revises: f7b1d3a84c62
Create Date: 2026-09-13
"""

from alembic import op
import sqlalchemy as sa


revision = "3e7a1c9d5b24"
down_revision = "f7b1d3a84c62"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("groups", sa.Column("interest_tags_json", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("groups", "interest_tags_json")
