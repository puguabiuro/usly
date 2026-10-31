"""Allow separate companion and organizer accounts with the same email.

Revision ID: 9e4a2c7b1d30
Revises: 8d3f1a6c9b20
"""

from alembic import op

revision = "9e4a2c7b1d30"
down_revision = "8d3f1a6c9b20"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_email")
        batch_op.create_index("ix_users_email", ["email"], unique=False)
        batch_op.create_unique_constraint(
            "uq_users_email_role", ["email", "role"]
        )


def downgrade():
    connection = op.get_bind()
    duplicate = connection.exec_driver_sql(
        "SELECT email FROM users "
        "GROUP BY email HAVING COUNT(*) > 1 LIMIT 1"
    ).first()

    if duplicate:
        raise RuntimeError(
            "Cannot restore global email uniqueness: "
            "multiple roles share an email address."
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint(
            "uq_users_email_role", type_="unique"
        )
        batch_op.drop_index("ix_users_email")
        batch_op.create_index("ix_users_email", ["email"], unique=True)
