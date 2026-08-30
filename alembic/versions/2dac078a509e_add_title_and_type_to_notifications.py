"""Add title and type to notifications

Revision ID: 2dac078a509e
Revises: ac2839c4ab12
Create Date: 2026-07-23 19:56:57.783415

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2dac078a509e'
down_revision: Union[str, Sequence[str], None] = 'ac2839c4ab12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Déclaration de l'Enum
    notification_type_enum = sa.Enum('BROADCAST', 'INDIVIDUEL', name='notificationtype')
    
    # 2. Création du type ENUM dans PostgreSQL s'il n'existe pas
    notification_type_enum.create(op.get_bind(), checkfirst=True)
    
    # 3. Ajout de la colonne title
    op.add_column('notifications', sa.Column('title', sa.String(length=500), nullable=True))
    
    # 4. Ajout de la colonne type avec le server_default pour les lignes existantes
    op.add_column(
        'notifications', 
        sa.Column(
            'type', 
            notification_type_enum, 
            nullable=False, 
            server_default='BROADCAST'
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('notifications', 'type')
    op.drop_column('notifications', 'title')
    
    # Suppression du type ENUM
    notification_type_enum = sa.Enum('BROADCAST', 'INDIVIDUEL', name='notificationtype')
    notification_type_enum.drop(op.get_bind(), checkfirst=True)