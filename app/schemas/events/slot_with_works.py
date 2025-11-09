from pydantic import ConfigDict, BaseModel, computed_field, Field  # <-- Import computed_field
from datetime import datetime
from uuid import UUID
from typing import List


class SlotWorkInfoSchema(BaseModel):
    id: UUID
    title: str
    track: str
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
    title: str

    model_config = ConfigDict(from_attributes=True)

    work_links: List[WorkSlotLinkSchema] = Field(default=[], exclude=True)

    @computed_field
    @property
    def works(self) -> List[SlotWorkInfoSchema]:
        if not self.work_links:
            return []

        return [
            link.work for link in self.work_links if link.work
        ]