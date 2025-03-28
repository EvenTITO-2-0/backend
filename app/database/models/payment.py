from enum import Enum

from sqlalchemy import ARRAY, UUID, Column, ForeignKey, Index, String

from app.database.models.base import Base
from app.database.models.utils import ModelTemplate


class PaymentStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    UNCOMPLETED = "UNCOMPLETED"
    PENDING_APPROVAL = "PENDING_APPROVAL"


class PaymentModel(ModelTemplate, Base):
    __tablename__ = "payments"

    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    inscription_id = Column(UUID(as_uuid=True), ForeignKey("inscriptions.id"), nullable=False)
    fare_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default=PaymentStatus.PENDING_APPROVAL)
    works = Column(ARRAY(UUID(as_uuid=True)), nullable=True)

    __table_args__ = (
        Index("ix_payment_event_id", "event_id"),
        Index("ix_payment_inscription_id", "inscription_id"),
    )
