from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.database.models.work import WorkStates
from app.schemas.works.author import AuthorInformation
from app.schemas.works.talk import Talk


class WorkUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    abstract: str
    keywords: list[str]
    authors: list[AuthorInformation]
    title: str


class TrackSchema(BaseModel):
    track: str


class WorkUpdateAdministrationSchema(TrackSchema):
    talk: Talk | None = None


class CreateWorkSchema(WorkUpdateSchema, TrackSchema):
    pass


class WorkStateSchema(BaseModel):
    state: WorkStates


class WorkWithState(CreateWorkSchema, WorkStateSchema, WorkUpdateAdministrationSchema):
    id: UUID
    deadline_date: datetime
    creation_date: datetime
    last_update: datetime
