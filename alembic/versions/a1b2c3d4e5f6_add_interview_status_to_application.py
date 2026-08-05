"""add interview status to applicationstatus enum

Revision ID: a1b2c3d4e5f6
Revises: dd691ca24cf8
Create Date: 2026-07-27 19:20:00.000000

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'dd691ca24cf8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    PostgreSQL ne permet pas de modifier un ENUM directement avec ALTER TYPE
    si la colonne est indexée. On procède en plusieurs étapes sûres.
    """
    # 1. Ajouter la nouvelle valeur à l'ENUM PostgreSQL
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'interview' AFTER 'PENDING'")


def downgrade() -> None:
    """
    PostgreSQL ne permet pas de supprimer une valeur d'un ENUM.
    Pour rétrograder, on recréerait le type sans la valeur 'interview'
    et on migrerait les données (ici on met juste un avertissement).
    """
    # NOTE: PostgreSQL ne supporte pas DROP VALUE sur un ENUM.
    # Pour rétrograder manuellement :
    # 1. Mettre à jour toutes les lignes status='interview' -> 'pending'
    # 2. Recréer le type ENUM sans 'interview'
    # 3. Réappliquer le type sur la colonne
    pass
