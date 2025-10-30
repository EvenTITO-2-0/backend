from pydantic import ConfigDict  # Use ConfigDict for Pydantic v2
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import List


class SlotWorkInfoSchema(BaseModel):
    id: UUID
    title: str

    model_config = ConfigDict(from_attributes=True)


class SlotWithWorksSchema(BaseModel):
    id: int
    start: datetime
    end: datetime
    room_name: str
    slot_type: str

    works: List[SlotWorkInfoSchema] = []

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, **kwargs):
        works_list = [
            SlotWorkInfoSchema.model_validate(link.work)
            for link in obj.work_links if link.work
        ]
        return super().model_validate({
            "id": obj.id,
            "start": obj.start,
            "end": obj.end,
            "room_name": obj.room_name,
            "slot_type": obj.slot_type,
            "works": works_list
        }, **kwargs)