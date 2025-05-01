from pydantic import ConfigDict, Field

from app.schemas.events.public_event import PublicEventSchema


class PublicEventWithRolesSchema(PublicEventSchema):
    model_config = ConfigDict(from_attributes=True)
    roles: list[str] = Field(examples=[["ORGANIZER"]], default_factory=list)
