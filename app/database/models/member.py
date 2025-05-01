from sqlalchemy import UUID, Column, ForeignKey
from sqlalchemy.orm import declarative_mixin, declared_attr

from app.database.models.utils import DateTemplate, UIDType


@declarative_mixin
class MemberModel(DateTemplate):
    @declared_attr
    def user_id(self):
        return Column(UIDType, ForeignKey("users.id"), primary_key=True)

    @declared_attr
    def event_id(self):
        return Column(UUID(as_uuid=True), ForeignKey("events.id"), primary_key=True)
