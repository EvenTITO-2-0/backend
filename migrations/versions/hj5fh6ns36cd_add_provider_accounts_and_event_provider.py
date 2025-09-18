# Nombre sugerido: add_provider_accounts_and_event_provider.py
"""add provider accounts and event provider

Revision ID: hj5fh6ns36cd
Revises: 0.0.1
Create Date: 2025-06-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'hj5fh6ns36cd'
down_revision: Union[str, None] = '78fa13572a99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear tabla provider_accounts
    op.create_table(
        'provider_accounts',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(), nullable=False, server_default='mercadopago'),
        sa.Column('access_token', sa.String(), nullable=False),
        sa.Column('refresh_token', sa.String(), nullable=False),
        sa.Column('public_key', sa.String(), nullable=False),
        sa.Column('account_id', sa.String(), nullable=False),
        sa.Column('account_status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('marketplace_fee', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('marketplace_fee_type', sa.String(), nullable=False, server_default='percentage'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Agregar columna provider_account_id a events
    op.add_column('events', sa.Column('provider_account_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_events_provider_account',
        'events', 'provider_accounts',
        ['provider_account_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_events_provider_account', 'events', type_='foreignkey')
    op.drop_column('events', 'provider_account_id')
    op.drop_table('provider_accounts')
