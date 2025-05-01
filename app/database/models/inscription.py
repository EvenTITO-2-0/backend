from enum import Enum
from typing import List

from sqlalchemy import ARRAY, UUID, Column, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base
from app.database.models.utils import ModelTemplate, UIDType


class InscriptionStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING_APPROVAL = "PENDING_APPROVAL"


class InscriptionRole(str, Enum):
    SPEAKER = "SPEAKER"
    ATTENDEE = "ATTENDEE"


class InscriptionModel(ModelTemplate, Base):
    __tablename__ = "inscriptions"

    user_id = Column(UIDType, ForeignKey("users.id"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    status = Column(String, default=InscriptionStatus.PENDING_APPROVAL.value, nullable=False)
    roles: Mapped[List[InscriptionRole]] = mapped_column(
        ARRAY(String), default=[InscriptionRole.ATTENDEE.value], nullable=False
    )
    affiliation = Column(String, default=None, nullable=True)

    # Always fetch the usermodel, when fetching a review
    user = relationship("UserModel", back_populates="inscriptions", lazy=False)

    __table_args__ = (
        Index("ix_inscription_user_id", "user_id"),
        Index("ix_inscription_event_id", "event_id"),
    )
