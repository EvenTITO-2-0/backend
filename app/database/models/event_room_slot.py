from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database.models.base import Base


class EventRoomSlotModel(Base):
    __tablename__ = 'event_room_slots'

    id = Column(Integer, primary_key=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    room_name = Column(String, nullable=False)
    slot_type = Column(String, nullable=False)
    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True), nullable=False)

