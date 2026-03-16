"""add templates to projects and team_members

Revision ID: add_templates_fields
Revises: 3e81a2a81f5e
Create Date: 2026-03-16 12:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_templates_fields'
down_revision: Union[str, Sequence[str], None] = '3e81a2a81f5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("projects",
        sa.Column("templates", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("team_members",
        sa.Column("templates", sa.JSON(), nullable=False, server_default="[]"))

def downgrade() -> None:
    op.drop_column("team_members", "templates")
    op.drop_column("projects", "templates")
