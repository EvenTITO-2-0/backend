from uuid import UUID

from pydantic import BaseModel

from app.schemas.events.roles import EventRole
from app.schemas.users.user import UserSchema
from app.schemas.users.utils import UID


class RolesRequestSchema(BaseModel):
    roles: list[EventRole]


class MemberRequestSchema(BaseModel):
    email: str
    role: EventRole


class MemberResponseSchema(BaseModel):
    event_id: UUID
    user_id: UID
    user: UserSchema


class MemberResponseWithRolesSchema(MemberResponseSchema):
    roles: list[str]
