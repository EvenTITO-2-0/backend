from datetime import datetime

from pydantic import BaseModel


class SlotSchema(BaseModel):
    """
    Schema for a single slot in the event's mdata.
    """

    title: str
    start: datetime  # FastAPI will parse the ISO string from the frontend
    end: datetime
    type: str
    room_name: str

    class Config:
        # Allows creating the schema from ORM models or dicts
        from_attributes = True
