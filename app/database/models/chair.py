from typing import List

from sqlalchemy import ARRAY, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base
from app.database.models.member import MemberModel


class ChairModel(MemberModel, Base):
    __tablename__ = "chairs"
    tracks: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)
