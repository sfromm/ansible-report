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
import json

taskhelper = sa.Table(
    'task',
    sa.MetaData(),
    sa.Column('id', sa.Integer()),
    sa.Column('hostname', sa.String()),
    sa.Column('module', sa.String()),
    sa.Column('result', sa.String()),
    sa.Column('data', sa.Text()),
    sa.Column('changed', sa.Boolean()),
    sa.Column('playbook_id', sa.Integer())
)

def upgrade():
    op.add_column('task',
                  sa.Column('changed', sa.Boolean, nullable=True))
    op.create_index('task_changed_idx', 'task', ['changed'])
    connection = op.get_bind()
    for task in connection.execute(taskhelper.select()):
        data = json.loads(task.data)
        changed = False
        if 'changed' in data:
            changed = data['changed']
        connection.execute(
            taskhelper.update().where(
                taskhelper.columns.id == task.id
            ).values(changed=changed)
        )

def downgrade():
    op.drop_column('task', 'changed')
    op.create_index('task_changed_idx')
