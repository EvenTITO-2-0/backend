"""create_event_room_slots_table

Revision ID: 2a44c3de0f39
Revises: 1a2b3c4d5e6f
Create Date: 2025-10-16 20:54:31.391182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a44c3de0f39'
down_revision: Union[str, None] = '1a2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'event_room_slots',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('event_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('room_name', sa.String(), nullable=False),
        sa.Column('slot_type', sa.String(), nullable=False),
        sa.Column('start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
    )


def downgrade() -> None:
    op.drop_table('event_room_slots')