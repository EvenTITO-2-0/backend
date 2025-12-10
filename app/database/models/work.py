import enum
from typing import List

from sqlalchemy import (
    ARRAY,
    JSON,
    UUID,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base
from app.database.models.utils import ModelTemplate, UIDType


class WorkStates(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RE_SUBMIT = "RE_SUBMIT"
    SUBMITTED = "SUBMITTED"


class WorkModel(ModelTemplate, Base):
    __tablename__ = "works"

    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    author_id = Column(UIDType, ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=False)
    track = Column(String, nullable=False)
    abstract = Column(String, nullable=False)
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    authors = Column(JSON, nullable=False)
    talk = Column(JSON, nullable=True)
    state = Column(String, nullable=False, default=WorkStates.SUBMITTED)
    deadline_date = Column(DateTime, nullable=False)
    work_number = Column(Integer, nullable=True)

    __table_args__ = (UniqueConstraint("event_id", "title", name="event_id_title_uc"),)

    reviewers = relationship("ReviewerModel", back_populates="work", lazy=True)
    reviews = relationship("ReviewModel", foreign_keys="[ReviewModel.work_id]", lazy=True)
    slot_links = relationship("WorkSlotModel", back_populates="work", lazy=True)
