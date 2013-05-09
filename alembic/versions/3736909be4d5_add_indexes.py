"""add indexes

Revision ID: 3736909be4d5
Revises: 53eddd07c597
Create Date: 2013-05-09 10:09:49.884197

"""

# revision identifiers, used by Alembic.
revision = '3736909be4d5'
down_revision = '53eddd07c597'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('task_timestamp_idx', 'task', ['timestamp'])
    op.create_index('task_hostname_idx', 'task', ['hostname'])
    op.create_index('task_module_idx', 'task', ['module'])
    op.create_index('task_result_idx', 'task', ['result'])
    op.create_index('user_username_idx', 'user', ['username'])
    op.create_index('playbook_path_idx', 'playbook', ['path'])
    op.create_index('playbook_uuid_idx', 'playbook', ['uuid'])
    op.create_index('playbook_connection_idx', 'playbook', ['connection'])
    op.create_index('playbook_starttime_idx', 'playbook', ['starttime'])

def downgrade():
    op.create_index('task_timestamp_idx')
    op.create_index('task_hostname_idx')
    op.create_index('task_module_idx')
    op.create_index('task_result_idx')
    op.create_index('user_username_idx')
    op.create_index('playbook_path_idx')
    op.create_index('playbook_uuid_idx')
    op.create_index('playbook_connection_idx')
    op.create_index('playbook_starttime_idx')
