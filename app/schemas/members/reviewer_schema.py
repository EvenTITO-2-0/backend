from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, PrivateAttr

from app.schemas.members.member_schema import MemberResponseSchema
from app.schemas.users.utils import UID
from app.schemas.works.review import ReviewResponseSchema
from app.schemas.works.work import WorkWithState


class ReviewerWithWorksResponseSchema(MemberResponseSchema):
    work_ids: list[UUID] = Field(
        max_length=100, examples=[["work_id_01", "work_id_02", "work_id_03"]], default_factory=list
    )


class ReviewerAssignmentSchema(BaseModel):
    review_deadline: datetime = Field(examples=[datetime.now()])
    work_id: UUID = Field(examples=["work_id_01"])


class ReviewerAssignmentWithWorkSchema(ReviewerAssignmentSchema):
    work: WorkWithState
    reviews: list[ReviewResponseSchema] = Field(default_factory=list)


class ReviewerResponseSchema(MemberResponseSchema, ReviewerAssignmentSchema):
    pass


class ReviewerRequestSchema(ReviewerAssignmentSchema):
    email: str
    _user_id: UID | None = PrivateAttr()


class ReviewerCreateRequestSchema(BaseModel):
    reviewers: list[ReviewerRequestSchema] = Field(max_length=50, default_factory=list)


class ReviewerUpdateRequestSchema(ReviewerAssignmentSchema):
    user_id: UID


class ReviewerWithWorksDeadlineResponseSchema(MemberResponseSchema):
    works: list[ReviewerAssignmentSchema] = Field(default_factory=list)
