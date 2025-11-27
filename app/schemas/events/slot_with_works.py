from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field  # <-- Import computed_field


class SlotWorkInfoSchema(BaseModel):
    id: UUID
    title: str
    track: str
    work_number: int | None = None
    model_config = ConfigDict(from_attributes=True)


class WorkSlotLinkSchema(BaseModel):
    work: SlotWorkInfoSchema | None = None
    model_config = ConfigDict(from_attributes=True)


class SlotWithWorksSchema(BaseModel):
    id: int
    start: datetime
    end: datetime
    room_name: str
    slot_type: str
    title: str | None = None

    model_config = ConfigDict(from_attributes=True)

    work_links: List[WorkSlotLinkSchema] = Field(default=[], exclude=True)

    @computed_field
    def works(self) -> List[SlotWorkInfoSchema]:
        if not self.work_links:
            return []

        return [link.work for link in self.work_links if link.work]
