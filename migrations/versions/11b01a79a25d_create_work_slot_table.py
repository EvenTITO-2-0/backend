"""create_work_slot_table

Revision ID: 11b01a79a25d
Revises: 2a44c3de0f39
Create Date: 2025-10-27 22:56:37.615180

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11b01a79a25d'
down_revision: Union[str, None] = '2a44c3de0f39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'work_slots',

        sa.Column('slot_id', sa.Integer, nullable=False),

        sa.Column('work_id', sa.UUID(as_uuid=True), nullable=False),

        sa.Column('creation_date', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_update', sa.DateTime(), server_default=sa.text('now()'), nullable=True),

        sa.ForeignKeyConstraint(['slot_id'], ['event_room_slots.id'], ),
        sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),

        sa.PrimaryKeyConstraint('slot_id', 'work_id')
    )

def downgrade() -> None:
    op.drop_table('work_slots')