"""add tasks table

Revision ID: add_tasks_table
Revises: 7c9850f22026
Create Date: 2025-12-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_tasks_table'
down_revision = '7c9850f22026'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True),
        sa.Column('task_type', sa.String(length=20), nullable=False),
        sa.Column('execution_type', sa.String(length=20), nullable=True),
        sa.Column('celery_task_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('task_args', sa.Text(), nullable=True),
        sa.Column('task_kwargs', sa.Text(), nullable=True),
        sa.Column('scheduled_time', sa.DateTime(), nullable=True),
        sa.Column('crontab_minute', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
        sa.Column('crontab_hour', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
        sa.Column('crontab_day_of_week', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
        sa.Column('crontab_day_of_month', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
        sa.Column('crontab_month_of_year', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('last_run_time', sa.DateTime(), nullable=True),
        sa.Column('next_run_time', sa.DateTime(), nullable=True),
        sa.Column('celery_task_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('owner_id', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_name'), 'tasks', ['name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tasks_name'), table_name='tasks')
    op.drop_table('tasks')
