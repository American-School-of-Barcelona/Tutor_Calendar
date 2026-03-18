"""add first_name and last_name to user

Revision ID: add_first_last_name_to_user
Revises: c4cb6b59775b
Create Date: 2026-03-18
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_first_last_name_to_user'
down_revision = 'c4cb6b59775b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('first_name', sa.String(length=80), nullable=True))
    op.add_column('user', sa.Column('last_name', sa.String(length=80), nullable=True))


def downgrade():
    op.drop_column('user', 'last_name')
    op.drop_column('user', 'first_name')