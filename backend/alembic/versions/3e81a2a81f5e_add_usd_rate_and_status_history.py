"""Add usd_rate and status history

Revision ID: 3e81a2a81f5e
Revises: d2e59c8cfef1
Create Date: 2026-03-14 13:27:53.201300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e81a2a81f5e'
down_revision: Union[str, Sequence[str], None] = 'd2e59c8cfef1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add usd_rate to expense_requests
    op.add_column('expense_requests', sa.Column('usd_rate', sa.Numeric(precision=18, scale=6), nullable=True))
    
    # Create expense_status_history table
    op.create_table('expense_status_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('expense_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('changed_by_id', sa.String(), nullable=True),
        sa.Column('changed_by_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['changed_by_id'], ['team_members.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['expense_id'], ['expense_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expense_status_history_expense_id'), 'expense_status_history', ['expense_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_expense_status_history_expense_id'), table_name='expense_status_history')
    op.drop_table('expense_status_history')
    op.drop_column('expense_requests', 'usd_rate')
