"""Merge heads: join audit migration with existing merge head

Revision ID: zz_merge_audit_heads
Revises: 8b46fdba24e3, zz_add_audit_logs_table
Create Date: 2026-08-01 10:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'zz_merge_audit_heads'
down_revision: Union[str, Sequence[str], None] = ('8b46fdba24e3', 'zz_add_audit_logs_table')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # merge-only migration; no DB schema changes
    pass


def downgrade() -> None:
    pass
