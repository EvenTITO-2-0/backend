from enum import Enum
from typing import List

from sqlalchemy import ARRAY, JSON, UUID, Column, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base
from app.database.models.utils import ModelTemplate, UIDType


class EventStatus(str, Enum):
    WAITING_APPROVAL = "WAITING_APPROVAL"
    NOT_APPROVED = "NOT_APPROVED"
    CREATED = "CREATED"
    STARTED = "STARTED"
    FINISHED = "FINISHED"
    SUSPENDED = "SUSPENDED"
    CANCELED = "CANCELED"
    BLOCKED = "BLOCKED"


class EventType(str, Enum):
    CONFERENCE = "CONFERENCE"
    TALK = "TALK"


class EventModel(ModelTemplate, Base):
    __tablename__ = "events"

    creator_id = Column(UIDType, ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=False, unique=True)
    description = Column(String)
    event_type = Column(String)
    status = Column(String, default=EventStatus.WAITING_APPROVAL)
    location = Column(String)
    tracks: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)
    notification_mails: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)
    review_skeleton = Column(JSON, default=None)
    pricing = Column(JSON, default=None)
    dates = Column(JSON)
    contact = Column(String, nullable=True)
    organized_by = Column(String, nullable=True)
    media: Mapped[List[JSON]] = mapped_column(ARRAY(JSON), default=None, nullable=True)
    mdata = Column(JSON, default=None)

    organizers = relationship("OrganizerModel", back_populates="event")
    creator = relationship("UserModel", back_populates="events", lazy=False)
    provider_account_id = Column(UUID(as_uuid=True), ForeignKey("provider_accounts.id"), nullable=True)
    payment_provider = relationship("ProviderAccountModel", back_populates="events")
