from pydantic import BaseModel, ConfigDict
from datetime import datetime


class EventRoomSlotSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_name: str
    slot_type: str
    start: datetime
    end: datetime

