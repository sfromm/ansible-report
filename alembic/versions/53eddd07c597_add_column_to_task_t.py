"""add column to task table

Revision ID: 53eddd07c597
Revises: 53fae050253c
Create Date: 2013-05-01 10:34:35.388559

"""

# revision identifiers, used by Alembic.
revision = '53eddd07c597'
down_revision = '53fae050253c'

from alembic import op
import sqlalchemy as sa
import logging


def upgrade():
    op.add_column('task',
            sa.Column('playbook_id', sa.Integer, nullable=True))
    try:
        op.create_foreign_key('fk_task_playbook', 'task', 'playbook',
                ['playbook_id'], ['id'])
    except NotImplementedError, e:
        logging.info("Failed to create foreign key constraint: %s", str(e))


def downgrade():
    op.drop_column('task', 'playbook_id')
