"""Add audit_logs table

Revision ID: zz_add_audit_logs_table
Revises: acacdf7e279e
Create Date: 2026-08-01 09:50:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'zz_add_audit_logs_table'
down_revision: Union[str, Sequence[str], None] = 'acacdf7e279e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('path', sa.String(length=1024), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
