"""refactor_user_model_and_repositories

Revision ID: 1ec9a05ce92a
Revises: 8bcc483cf9ea
Create Date: 2026-04-11 14:39:44.710815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '1ec9a05ce92a'
down_revision: Union[str, Sequence[str], None] = '8bcc483cf9ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Create new tables (idempotent)
    if 'users' not in existing_tables:
        op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('login', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('position', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('telegram_chat_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('team', sa.String(), nullable=True),
        sa.Column('templates', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        existing_users_indexes = []
    else:
        existing_users_indexes = [idx['name'] for idx in inspector.get_indexes('users')]

    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'ix_users_login' not in existing_users_indexes:
            batch_op.create_index(batch_op.f('ix_users_login'), ['login'], unique=True)
        if 'ix_users_role' not in existing_users_indexes:
            batch_op.create_index(batch_op.f('ix_users_role'), ['role'], unique=False)
        if 'ix_users_status' not in existing_users_indexes:
            batch_op.create_index(batch_op.f('ix_users_status'), ['status'], unique=False)
        if 'ix_users_telegram_chat_id' not in existing_users_indexes:
            batch_op.create_index(batch_op.f('ix_users_telegram_chat_id'), ['telegram_chat_id'], unique=True)

    if 'branches' not in existing_tables:
        op.create_table('branches',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
        existing_branches_indexes = []
    else:
        existing_branches_indexes = [idx['name'] for idx in inspector.get_indexes('branches')]

    with op.batch_alter_table('branches', schema=None) as batch_op:
        if 'ix_branches_code' not in existing_branches_indexes:
            batch_op.create_index(batch_op.f('ix_branches_code'), ['code'], unique=True)

    if 'user_projects' not in existing_tables:
        op.create_table('user_projects',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'project_id')
        )

    if 'user_branches' not in existing_tables:
        op.create_table('user_branches',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('branch_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'branch_id')
        )

    # 2. Migrate data from team_members to users (only if team_members still exists)
    if 'team_members' in existing_tables and 'users' not in existing_tables:
        op.execute("""
            INSERT INTO users (id, last_name, first_name, login, password_hash, position, telegram_chat_id, status, team, templates, created_at, role)
            SELECT id, last_name, first_name, login, password_hash, position, telegram_chat_id, status, team, templates, created_at, 'user'
            FROM team_members
        """)

    # 3. Add new columns to expense_requests if missing
    existing_expense_cols = [c['name'] for c in inspector.get_columns('expense_requests')]
    existing_expense_indexes = [idx['name'] for idx in inspector.get_indexes('expense_requests')]

    with op.batch_alter_table('expense_requests', schema=None) as batch_op:
        if 'branch_id' not in existing_expense_cols:
            batch_op.add_column(sa.Column('branch_id', sa.String(), nullable=True))
        if 'branch_name' not in existing_expense_cols:
            batch_op.add_column(sa.Column('branch_name', sa.String(), nullable=True))
        if 'branch_code' not in existing_expense_cols:
            batch_op.add_column(sa.Column('branch_code', sa.String(), nullable=True))
        if 'ix_expense_requests_branch_id' not in existing_expense_indexes:
            batch_op.create_index(batch_op.f('ix_expense_requests_branch_id'), ['branch_id'], unique=False)
        batch_op.create_foreign_key('fk_expense_requests_created_by_id', 'users', ['created_by_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_expense_requests_branch_id', 'branches', ['branch_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('expense_status_history', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_expense_status_history_changed_by_id', 'users', ['changed_by_id'], ['id'], ondelete='SET NULL')

    existing_project_cols = [c['name'] for c in inspector.get_columns('projects')]
    existing_project_indexes = [idx['name'] for idx in inspector.get_indexes('projects')]
    with op.batch_alter_table('projects', schema=None) as batch_op:
        if 'category' not in existing_project_cols:
            batch_op.add_column(sa.Column('category', sa.String(), nullable=True))
        if 'ix_projects_category' not in existing_project_indexes:
            batch_op.create_index(batch_op.f('ix_projects_category'), ['category'], unique=False)

    # 4. Migrate associations (only if source tables exist)
    if 'member_projects' in existing_tables and 'user_projects' in existing_tables:
        op.execute("INSERT INTO user_projects (user_id, project_id) SELECT member_id, project_id FROM member_projects")

    # 5. Drop old tables (only if they still exist)
    if 'member_projects' in existing_tables:
        op.drop_table('member_projects')
    if 'team_members' in existing_tables:
        op.drop_table('team_members')


def downgrade() -> None:
    # Minimal downgrade support
    op.create_table('team_members',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('last_name', sa.String(), nullable=False),
    sa.Column('first_name', sa.String(), nullable=False),
    sa.Column('login', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.Column('position', sa.String(), nullable=True),
    sa.Column('telegram_chat_id', sa.BigInteger(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('team', sa.String(), nullable=True),
    sa.Column('templates', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.execute("""
        INSERT INTO team_members (id, last_name, first_name, login, password_hash, position, telegram_chat_id, status, team, templates, created_at)
        SELECT id, last_name, first_name, login, password_hash, position, telegram_chat_id, status, team, templates, created_at
        FROM users
    """)
    op.drop_table('user_branches')
    op.drop_table('user_projects')
    op.drop_table('branches')
    op.drop_table('users')
