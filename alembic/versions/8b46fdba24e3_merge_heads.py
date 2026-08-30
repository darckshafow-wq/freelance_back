"""merge heads

Revision ID: 8b46fdba24e3
Revises: 2e998efa0c06, b2c3d4e5f6a7
Create Date: 2026-07-31 20:05:22.368983

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b46fdba24e3'
down_revision: Union[str, Sequence[str], None] = ('2e998efa0c06', 'b2c3d4e5f6a7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
