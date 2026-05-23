"""add missing tables for current models

Revision ID: 1f534ab4a54f
Revises: 6d9d8c4a1b7e
Create Date: 2026-04-22 19:37:35.070527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f534ab4a54f'
down_revision: Union[str, Sequence[str], None] = '6d9d8c4a1b7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(table_name)


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(ix.get("name") == index_name for ix in inspector.get_indexes(table_name))


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str], unique: bool = False) -> None:
    if not _table_exists(table_name):
        return
    if _index_exists(table_name, index_name):
        return
    op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    """Upgrade schema."""

    if not _table_exists('password_reset_tokens'):
        op.create_table(
            'password_reset_tokens',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('token', sa.String(length=255), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
    _create_index_if_missing('ix_password_reset_tokens_created_at', 'password_reset_tokens', ['created_at'])
    _create_index_if_missing('ix_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'])
    _create_index_if_missing('ix_password_reset_tokens_token', 'password_reset_tokens', ['token'], unique=True)
    _create_index_if_missing('ix_password_reset_tokens_used_at', 'password_reset_tokens', ['used_at'])
    _create_index_if_missing('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    _create_index_if_missing('ix_password_reset_tokens_user_used', 'password_reset_tokens', ['user_id', 'used_at'])

    if not _table_exists('user_blocks'):
        op.create_table(
            'user_blocks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('blocker_user_id', sa.Integer(), nullable=False),
            sa.Column('blocked_user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint('blocker_user_id <> blocked_user_id', name='ck_user_blocks_no_self'),
            sa.ForeignKeyConstraint(['blocked_user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['blocker_user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('blocker_user_id', 'blocked_user_id', name='uq_user_blocks_blocker_blocked'),
        )
    _create_index_if_missing('ix_user_blocks_blocked_created', 'user_blocks', ['blocked_user_id', 'created_at'])
    _create_index_if_missing('ix_user_blocks_blocked_user_id', 'user_blocks', ['blocked_user_id'])
    _create_index_if_missing('ix_user_blocks_blocker_created', 'user_blocks', ['blocker_user_id', 'created_at'])
    _create_index_if_missing('ix_user_blocks_blocker_user_id', 'user_blocks', ['blocker_user_id'])
    _create_index_if_missing('ix_user_blocks_created_at', 'user_blocks', ['created_at'])

    if not _table_exists('event_saves'):
        op.create_table(
            'event_saves',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('event_id', 'user_id', name='uq_event_saves_event_user'),
        )
    _create_index_if_missing('ix_event_saves_event_id', 'event_saves', ['event_id'])
    _create_index_if_missing('ix_event_saves_event_user', 'event_saves', ['event_id', 'user_id'])
    _create_index_if_missing('ix_event_saves_user_id', 'event_saves', ['user_id'])

    if not _table_exists('group_invitations'):
        op.create_table(
            'group_invitations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('group_id', sa.Integer(), nullable=False),
            sa.Column('inviter_user_id', sa.Integer(), nullable=False),
            sa.Column('invitee_user_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
            sa.CheckConstraint("status IN ('pending','accepted','rejected')", name='ck_group_invitations_status'),
            sa.CheckConstraint('inviter_user_id <> invitee_user_id', name='ck_group_invitations_no_self'),
            sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['invitee_user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['inviter_user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('group_id', 'invitee_user_id', name='uq_group_invitations_group_invitee'),
        )
    _create_index_if_missing('ix_group_invitations_created_at', 'group_invitations', ['created_at'])
    _create_index_if_missing('ix_group_invitations_group_id', 'group_invitations', ['group_id'])
    _create_index_if_missing('ix_group_invitations_invitee_status', 'group_invitations', ['invitee_user_id', 'status'])
    _create_index_if_missing('ix_group_invitations_invitee_user_id', 'group_invitations', ['invitee_user_id'])
    _create_index_if_missing('ix_group_invitations_inviter_status', 'group_invitations', ['inviter_user_id', 'status'])
    _create_index_if_missing('ix_group_invitations_inviter_user_id', 'group_invitations', ['inviter_user_id'])
    _create_index_if_missing('ix_group_invitations_status', 'group_invitations', ['status'])

    if not _table_exists('user_notifications'):
        op.create_table(
            'user_notifications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.Integer(), nullable=True),
            sa.Column('partner_user_id', sa.Integer(), nullable=True),
            sa.Column('type', sa.String(length=40), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['partner_user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
    _create_index_if_missing('ix_user_notifications_event_id', 'user_notifications', ['event_id'])
    _create_index_if_missing('ix_user_notifications_partner_user_id', 'user_notifications', ['partner_user_id'])
    _create_index_if_missing('ix_user_notifications_user_id', 'user_notifications', ['user_id'])

def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index('ix_user_notifications_user_id', table_name='user_notifications')
    op.drop_index('ix_user_notifications_partner_user_id', table_name='user_notifications')
    op.drop_index('ix_user_notifications_event_id', table_name='user_notifications')
    op.drop_table('user_notifications')

    op.drop_index('ix_group_invitations_status', table_name='group_invitations')
    op.drop_index('ix_group_invitations_inviter_user_id', table_name='group_invitations')
    op.drop_index('ix_group_invitations_inviter_status', table_name='group_invitations')
    op.drop_index('ix_group_invitations_invitee_user_id', table_name='group_invitations')
    op.drop_index('ix_group_invitations_invitee_status', table_name='group_invitations')
    op.drop_index('ix_group_invitations_group_id', table_name='group_invitations')
    op.drop_index('ix_group_invitations_created_at', table_name='group_invitations')
    op.drop_table('group_invitations')

    op.drop_index('ix_event_saves_user_id', table_name='event_saves')
    op.drop_index('ix_event_saves_event_user', table_name='event_saves')
    op.drop_index('ix_event_saves_event_id', table_name='event_saves')
    op.drop_table('event_saves')

    op.drop_index('ix_user_blocks_created_at', table_name='user_blocks')
    op.drop_index('ix_user_blocks_blocker_user_id', table_name='user_blocks')
    op.drop_index('ix_user_blocks_blocker_created', table_name='user_blocks')
    op.drop_index('ix_user_blocks_blocked_user_id', table_name='user_blocks')
    op.drop_index('ix_user_blocks_blocked_created', table_name='user_blocks')
    op.drop_table('user_blocks')

    op.drop_index('ix_password_reset_tokens_user_used', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_user_id', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_used_at', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_token', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_expires_at', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_created_at', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
