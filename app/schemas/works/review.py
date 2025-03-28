from datetime import datetime
from enum import Enum
from typing import Self, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.database.models.work import WorkStates
from app.schemas.events.review_skeleton.multiples_choice_question import MultipleChoiceAnswer
from app.schemas.events.review_skeleton.rating_question import RatingAnswer
from app.schemas.events.review_skeleton.simple_question import SimpleAnswer
from app.schemas.storage.schemas import DownloadURLSchema, UploadURLSchema
from app.schemas.users.user import PublicUserSchema
from app.schemas.users.utils import UID


class ReviewDecision(str, Enum):
    APPROVED = "APPROVED"
    NOT_APPROVED = "NOT_APPROVED"
    RE_SUBMIT = "RE_SUBMIT"


class ReviewAnswer(BaseModel):
    answers: list[Union[MultipleChoiceAnswer, SimpleAnswer, RatingAnswer]] = Field(default_factory=list)


class ReviewCreateRequestSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: ReviewDecision = Field(examples=["APPROVED"])
    review: ReviewAnswer


class ReviewResponseSchema(ReviewCreateRequestSchema):
    id: UUID = Field(examples=["review_id_01"])
    event_id: UUID = Field(examples=["event_id_01"])
    work_id: UUID = Field(examples=["work_id_01"])
    submission_id: UUID = Field(examples=["submission_id_01"])
    reviewer_id: UID = Field(examples=["user_id_01"])
    reviewer: PublicUserSchema
    creation_date: datetime
    last_update: datetime


class ReviewDownloadSchema(ReviewResponseSchema):
    model_config = ConfigDict(from_attributes=True)
    download_url: DownloadURLSchema


class ReviewUploadSchema(ReviewResponseSchema):
    model_config = ConfigDict(from_attributes=True)
    upload_url: UploadURLSchema


class ReviewPublishSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reviews_to_publish: list[UUID] = Field(examples=[["review_id_1", "review_id_2", "review_id_n"]])
    new_work_status: WorkStates = Field(examples=[WorkStates.APPROVED])
    resend_deadline: datetime | None = Field(examples=[datetime.now()], default=None)

    @model_validator(mode="after")
    def check_answers(self) -> Self:
        if self.new_work_status == WorkStates.RE_SUBMIT and self.resend_deadline is None:
            raise ValueError("resend_deadline cannot be None if new work status is RE_SUBMIT")
        return self
