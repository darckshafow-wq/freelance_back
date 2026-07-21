"""Add reviewee_id to reviews table

Revision ID: f3a9c12d4e5b
Revises: 2d66501e76ce
Create Date: 2026-07-20 20:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f3a9c12d4e5b'
down_revision: Union[str, Sequence[str], None] = '2d66501e76ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajoute la colonne reviewee_id (FK → users.id, nullable) à la table reviews."""
    op.add_column(
        'reviews',
        sa.Column('reviewee_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_reviews_reviewee_id_users',
        'reviews', 'users',
        ['reviewee_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index(op.f('ix_reviews_reviewee_id'), 'reviews', ['reviewee_id'], unique=False)


def downgrade() -> None:
    """Retire reviewee_id de la table reviews."""
    op.drop_index(op.f('ix_reviews_reviewee_id'), table_name='reviews')
    op.drop_constraint('fk_reviews_reviewee_id_users', 'reviews', type_='foreignkey')
    op.drop_column('reviews', 'reviewee_id')
