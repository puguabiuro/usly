"""Add consumed account-link proof records.

Revision ID: 8d3f1a6c9b20
Revises: 7c9e2a4b6d10
"""

from alembic import op
import sqlalchemy as sa


revision = "8d3f1a6c9b20"
down_revision = "7c9e2a4b6d10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "account_link_proof_uses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("proof_id", sa.String(length=64), nullable=False),
        sa.Column("initiating_user_id", sa.Integer(), nullable=False),
        sa.Column("second_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "consumed_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["initiating_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["second_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "proof_id",
            name="uq_account_link_proof_uses_proof_id",
        ),
        sa.CheckConstraint(
            "initiating_user_id <> second_user_id",
            name="ck_account_link_proof_uses_distinct_users",
        ),
    )


def downgrade():
    op.drop_table("account_link_proof_uses")
