"""add task_executions table

Revision ID: add_task_executions
Revises: add_tasks_table
Create Date: 2025-12-02 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision = 'add_task_executions'
down_revision = 'add_tasks_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create task_executions table
    op.create_table(
        'task_executions',
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('celery_task_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('traceback', sa.Text(), nullable=True),
        sa.Column('args', sa.Text(), nullable=True),
        sa.Column('kwargs', sa.Text(), nullable=True),
        sa.Column('worker', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('runtime', sa.Float(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_executions_celery_task_id'), 'task_executions', ['celery_task_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_task_executions_celery_task_id'), table_name='task_executions')
    op.drop_table('task_executions')
