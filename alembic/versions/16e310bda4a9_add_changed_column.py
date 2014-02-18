"""add changed column

Revision ID: 16e310bda4a9
Revises: 3736909be4d5
Create Date: 2014-02-17 22:17:35.752109

"""

# revision identifiers, used by Alembic.
revision = '16e310bda4a9'
down_revision = '3736909be4d5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('task',
                  sa.Column('changed', sa.Boolean, nullable=True))
    op.create_index('task_changed_idx', 'task', ['changed'])


def downgrade():
    op.drop_column('task', 'changed')
    op.create_index('task_changed_idx')
