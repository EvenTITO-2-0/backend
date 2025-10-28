from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy import Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from .base import Base
from .utils import DateTemplate


class WorkSlotModel(DateTemplate, Base):
    __tablename__ = 'work_slots'

    slot_id = Column(Integer, ForeignKey("event_room_slots.id"), nullable=False, primary_key=True)
    work_id = Column(UUID(as_uuid=True), ForeignKey("works.id"), nullable=False, primary_key=True)

    slot = relationship("EventRoomSlotModel", back_populates="work_links")
    work = relationship("WorkModel", back_populates="slot_links")

    __table_args__ = (
        UniqueConstraint('slot_id', 'work_id', name='_slot_work_uc'),
    )

