"""update provider accounts constraints and add payment metadata

Revision ID: 1a2b3c4d5e6f
Revises: hj5fh6ns36cd
Create Date: 2025-09-18
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = 'hj5fh6ns36cd'
branch_labels = None
depends_on = None


def upgrade():
    # provider_accounts: drop unique on user_id (assumes default name from PG)
    try:
        op.drop_constraint('provider_accounts_user_id_key', 'provider_accounts', type_='unique')
    except Exception:
        # In case the constraint has a different name, ignore silently
        pass

    # provider_accounts: add unique on (provider, account_id)
    op.create_unique_constraint('uq_provider_accounts_provider_account', 'provider_accounts', ['provider', 'account_id'])

    # payments: add amount, currency, provider_preference_id, provider_payment_id
    op.add_column('payments', sa.Column('amount', sa.Float(), nullable=True))
    op.add_column('payments', sa.Column('currency', sa.String(), nullable=True))
    op.add_column('payments', sa.Column('provider_preference_id', sa.String(), nullable=True))
    op.add_column('payments', sa.Column('provider_payment_id', sa.String(), nullable=True))


def downgrade():
    # payments: drop new columns
    op.drop_column('payments', 'provider_payment_id')
    op.drop_column('payments', 'provider_preference_id')
    op.drop_column('payments', 'currency')
    op.drop_column('payments', 'amount')

    # provider_accounts: drop unique on (provider, account_id)
    op.drop_constraint('uq_provider_accounts_provider_account', 'provider_accounts', type_='unique')

    # provider_accounts: recreate unique on user_id
    op.create_unique_constraint('provider_accounts_user_id_key', 'provider_accounts', ['user_id'])


