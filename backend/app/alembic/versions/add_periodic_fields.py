"""Add periodic schedule fields to tasks

Revision ID: add_periodic_fields
Revises: add_task_executions
Create Date: 2025-12-03

"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'add_periodic_fields'
down_revision: Union[str, None] = 'add_task_executions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add periodic_schedule_type column
    op.add_column('tasks', sa.Column('periodic_schedule_type', sa.String(length=20), nullable=True))
    
    # Add interval fields
    op.add_column('tasks', sa.Column('interval_seconds', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('interval_minutes', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('interval_hours', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('interval_days', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove columns in reverse order
    op.drop_column('tasks', 'interval_days')
    op.drop_column('tasks', 'interval_hours')
    op.drop_column('tasks', 'interval_minutes')
    op.drop_column('tasks', 'interval_seconds')
    op.drop_column('tasks', 'periodic_schedule_type')
