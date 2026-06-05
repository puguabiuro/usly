"""add event interest tags json

Revision ID: a6f4c2d9e801
Revises: f1b7c9a2d441
Create Date: 2026-06-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a6f4c2d9e801"
down_revision = "f1b7c9a2d441"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("events", sa.Column("interest_tags_json", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("events", "interest_tags_json")
