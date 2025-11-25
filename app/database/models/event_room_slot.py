from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class EventRoomSlotModel(Base):
    __tablename__ = "event_room_slots"
    available_space = 0  # se usa en el algoritmo de busqueda de solucion

    id = Column(Integer, primary_key=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    room_name = Column(String, nullable=False)
    title = Column(String, nullable=True)
    slot_type = Column(String, nullable=False)
    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True), nullable=False)

    event = relationship("EventModel", back_populates="event_slots")

    work_links = relationship(
        "WorkSlotModel", back_populates="slot", lazy="selectin", cascade="all, delete-orphan", passive_deletes=True
    )
