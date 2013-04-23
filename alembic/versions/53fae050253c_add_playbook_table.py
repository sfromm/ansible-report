"""add playbook table

Revision ID: 53fae050253c
Revises: 2f3bd55d88a
Create Date: 2013-04-22 22:59:21.598422

"""

# revision identifiers, used by Alembic.
revision = '53fae050253c'
down_revision = '2f3bd55d88a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('playbook',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('path', sa.String(), nullable=True),
        sa.Column('uuid', sa.String(), nullable=True),
        sa.Column('connection', sa.String(), nullable=True),
        sa.Column('starttime', sa.DateTime(), nullable=True),
        sa.Column('endtime', sa.DateTime(), nullable=True),
        sa.Column('checksum', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('playbook')
