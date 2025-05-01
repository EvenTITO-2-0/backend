from sqlalchemy import UUID, Column, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database.models.base import Base
from app.database.models.member import MemberModel


class ReviewerModel(MemberModel, Base):
    __tablename__ = "reviewers"
    work_id = Column(UUID(as_uuid=True), ForeignKey("works.id"), primary_key=True)
    review_deadline = Column(DateTime, nullable=False)

    work = relationship("WorkModel", back_populates="reviewers", lazy=True)
