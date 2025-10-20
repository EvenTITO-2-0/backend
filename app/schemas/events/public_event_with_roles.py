from app.schemas.events.event_room_slot import EventRoomSlotSchema
from app.schemas.events.public_event import PublicEventSchema
from pydantic import ConfigDict, Field


class PublicEventWithRolesSchema(PublicEventSchema):
    model_config = ConfigDict(from_attributes=True)
    roles: list[str] = Field(examples=[["ORGANIZER"]], default_factory=list)
    event_slots: list[EventRoomSlotSchema] = Field(default_factory=list)
