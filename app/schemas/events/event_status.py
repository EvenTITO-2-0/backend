from pydantic import BaseModel, Field

from app.database.models.event import EventStatus


class EventStatusSchema(BaseModel):
    status: EventStatus = Field(examples=[EventStatus.WAITING_APPROVAL])
