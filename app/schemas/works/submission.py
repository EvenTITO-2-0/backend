from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.database.models.work import WorkStates
from app.schemas.storage.schemas import DownloadURLSchema, UploadURLSchema


class SubmissionDatesResponseSchema(BaseModel):
    creation_date: datetime
    last_update: datetime


class SubmissionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    work_id: UUID
    event_id: UUID
    state: WorkStates


class SubmissionResponseSchema(SubmissionSchema, SubmissionDatesResponseSchema):
    pass


class SubmissionDownloadSchema(SubmissionResponseSchema):
    model_config = ConfigDict(from_attributes=True)
    download_url: DownloadURLSchema


class SubmissionUploadSchema(SubmissionSchema):
    model_config = ConfigDict(from_attributes=True)
    upload_url: UploadURLSchema
