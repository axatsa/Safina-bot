"""refactor_user_model_and_repositories

Revision ID: 1ec9a05ce92a
Revises: 8bcc483cf9ea
Create Date: 2026-04-11 14:39:44.710815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '1ec9a05ce92a'
down_revision: Union[str, Sequence[str], None] = '8bcc483cf9ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create new tables first
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
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_login'), ['login'], unique=True)
        batch_op.create_index(batch_op.f('ix_users_role'), ['role'], unique=False)
        batch_op.create_index(batch_op.f('ix_users_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_users_telegram_chat_id'), ['telegram_chat_id'], unique=True)

    op.create_table('branches',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('project_id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('branches', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_branches_code'), ['code'], unique=True)

    op.create_table('user_projects',
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('project_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'project_id')
    )
    op.create_table('user_branches',
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('branch_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'branch_id')
    )

    # 2. Migrate basic data from team_members to users
    op.execute("""
        INSERT INTO users (id, last_name, first_name, login, password_hash, position, telegram_chat_id, status, team, templates, created_at, role)
        SELECT id, last_name, first_name, login, password_hash, position, telegram_chat_id, status, team, templates, created_at, 'user'
        FROM team_members
    """)

    # 3. Update existing tables while team_members STILL exists to satisfy FK reflection
    with op.batch_alter_table('expense_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('branch_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('branch_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('branch_code', sa.String(), nullable=True))
        batch_op.create_index(batch_op.f('ix_expense_requests_branch_id'), ['branch_id'], unique=False)
        # Note: We'll link to 'users' table in the new schema later or trust the rename.
        # Actually, in batch mode we replace the FK.
        # batch_op.drop_constraint(...) # This might fail if name is unknown
        batch_op.create_foreign_key('fk_expense_requests_created_by_id', 'users', ['created_by_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_expense_requests_branch_id', 'branches', ['branch_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('expense_status_history', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_expense_status_history_changed_by_id', 'users', ['changed_by_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(), nullable=True))
        batch_op.create_index(batch_op.f('ix_projects_category'), ['category'], unique=False)

    # 4. Migrate associations
    op.execute("INSERT INTO user_projects (user_id, project_id) SELECT member_id, project_id FROM member_projects")

    # 5. Finally drop old tables
    op.drop_table('member_projects')
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
