from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.events.event_status import EventStatusSchema
from app.schemas.events.review_skeleton.review_skeleton import ReviewSkeletonResponseSchema
from app.schemas.events.schemas import DynamicEventSchema, StaticEventSchema
from app.schemas.media.image import ImgSchema
from app.schemas.users.utils import UID
from app.services.storage.event_storage_service import EventsStorageService


class PublicEventSchema(StaticEventSchema, DynamicEventSchema, ReviewSkeletonResponseSchema, EventStatusSchema):
    id: UUID

    @computed_field
    def media(self) -> list[ImgSchema]:
        return EventsStorageService.get_media(self.id)


class EventCreatorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UID
    name: str = Field(exclude=True)
    lastname: str = Field(exclude=True)
    email: str = Field(examples=["jose.perez@email.com"])

    @computed_field
    def fullname(self) -> str:
        return self.name + " " + self.lastname


class PublicEventWithCreatorSchema(PublicEventSchema):
    model_config = ConfigDict(from_attributes=True)
    creator: EventCreatorSchema | None = Field(default=None)
