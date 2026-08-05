"""add INTERVIEW uppercase to applicationstatus enum

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-27 19:38:00.000000

"""
from typing import Sequence, Union
from alembic import op


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Ajoute la valeur 'INTERVIEW' en majuscules (cohérent avec PENDING/ACCEPTED/REJECTED).
    La valeur 'interview' minuscule ajoutée précédemment reste dans l'ENUM mais est inutilisée.
    """
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'INTERVIEW' AFTER 'PENDING'")


def downgrade() -> None:
    # PostgreSQL ne supporte pas DROP VALUE sur un ENUM — pas de rollback automatique.
    pass
