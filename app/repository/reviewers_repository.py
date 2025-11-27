from uuid import UUID

from sqlalchemy import and_, exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database.models.review import ReviewModel
from app.database.models.reviewer import ReviewerModel
from app.database.models.user import UserModel
from app.database.models.work import WorkModel
from app.repository.members_repository import MemberRepository
from app.schemas.members.reviewer_schema import (
    ReviewerAssignmentWithWorkSchema,
    ReviewerResponseSchema,
    ReviewerUpdateRequestSchema,
    ReviewerWithWorksDeadlineResponseSchema,
    ReviewerWithWorksResponseSchema,
)
from app.schemas.users.utils import UID
from app.schemas.works.review import ReviewResponseSchema
from app.schemas.works.work import WorkWithState


class ReviewerRepository(MemberRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ReviewerModel)

    def _primary_key_conditions(self, primary_key):
        event_id, reviewer_id, work_id = primary_key
        return [
            ReviewerModel.event_id == event_id,
            ReviewerModel.user_id == reviewer_id,
            ReviewerModel.work_id == work_id,
        ]

    async def is_reviewer_of_work_in_event(self, event_id: UUID, user_id: UID, work_id: UUID) -> bool:
        return await self.exists((event_id, user_id, work_id))

    async def is_reviewer_in_event(self, event_id: UUID, user_id: UID) -> bool:
        query = select(exists().where(and_(ReviewerModel.event_id == event_id, ReviewerModel.user_id == user_id)))
        result = await self.session.execute(query)
        return result.scalar()

    async def get_all_reviewers(
        self, event_id: UUID, work_id: UUID | None
    ) -> list[ReviewerWithWorksDeadlineResponseSchema]:
        filters = [ReviewerModel.event_id == event_id]
        if work_id is not None:
            filters.append(ReviewerModel.work_id == work_id)
        query = (
            select(
                ReviewerModel.event_id.label("event_id"),
                ReviewerModel.user_id.label("user_id"),
                UserModel,
                func.json_agg(
                    func.json_build_object(
                        "work_id", ReviewerModel.work_id, "review_deadline", ReviewerModel.review_deadline
                    )
                ).label("works"),
            )
            .join(UserModel, ReviewerModel.user_id == UserModel.id)
            .filter(and_(*filters))
            .group_by(UserModel.id, ReviewerModel.user_id, ReviewerModel.event_id)
        )

        result = await self.session.execute(query)
        res = result.fetchall()
        return [
            ReviewerWithWorksDeadlineResponseSchema(
                event_id=row.event_id, user_id=row.user_id, user=row.UserModel, works=row.works
            )
            for row in res
        ]

    async def get_reviewer_by_user_id(self, event_id: UUID, user_id: UID) -> ReviewerWithWorksResponseSchema:
        group_by_subquery = (
            select(
                ReviewerModel.event_id,
                ReviewerModel.user_id,
                func.array_agg(ReviewerModel.work_id).label("work_ids"),
            )
            .where(and_(ReviewerModel.event_id == event_id, ReviewerModel.user_id == user_id))
            .group_by(ReviewerModel.event_id, ReviewerModel.user_id)
        ).subquery()

        query = select(
            group_by_subquery.c.event_id, group_by_subquery.c.user_id, group_by_subquery.c.work_ids, UserModel
        ).join(UserModel, group_by_subquery.c.user_id == UserModel.id)
        result = await self.session.execute(query)
        res = result.fetchone()
        return ReviewerWithWorksResponseSchema(
            event_id=res.event_id, work_ids=res.work_ids, user_id=res.user_id, user=res.UserModel
        )

    async def get_reviewer_by_work_id(self, event_id: UUID, user_id: UID, work_id: UUID) -> ReviewerResponseSchema:
        query = select(UserModel, self.model).where(
            and_(
                self.model.event_id == event_id,
                self.model.user_id == user_id,
                self.model.work_id == work_id,
                self.model.user_id == UserModel.id,
            )
        )
        result = await self.session.execute(query)
        user, model = result.fetchone()
        return ReviewerResponseSchema(
            event_id=model.event_id,
            work_id=model.work_id,
            user_id=model.user_id,
            review_deadline=model.review_deadline,
            user=user,
        )

    async def create_reviewers(self, event_id: UUID, reviewers) -> None:
        for new_reviewer in reviewers:
            new_reviewer_model = ReviewerModel(
                event_id=event_id,
                work_id=new_reviewer.work_id,
                user_id=new_reviewer._user_id,
                review_deadline=new_reviewer.review_deadline,
            )
            self.session.add(new_reviewer_model)
        await self.session.commit()

    async def update_reviewer(self, event_id: UUID, update_schema: ReviewerUpdateRequestSchema) -> None:
        conditions = [
            ReviewerModel.event_id == event_id,
            ReviewerModel.user_id == update_schema.user_id,
            ReviewerModel.work_id == update_schema.work_id,
        ]
        query = update(self.model).where(and_(*conditions)).values(review_deadline=update_schema.review_deadline)
        await self.session.execute(query)
        await self.session.commit()

    async def get_assignments(self, event_id: UUID, user_id: UID):
        query = (
            select(ReviewerModel)
            .options(
                joinedload(ReviewerModel.work).joinedload(WorkModel.reviews).joinedload(ReviewModel.reviewer)
            )
            .where(and_(ReviewerModel.event_id == event_id, ReviewerModel.user_id == user_id))
        )

        result = await self.session.execute(query)
        res = result.unique().scalars().all()
        return [
            ReviewerAssignmentWithWorkSchema(
                work_id=row.work_id,
                review_deadline=row.review_deadline,
                work=WorkWithState(**row.work.__dict__),
                reviews=[
                    ReviewResponseSchema(
                        id=review.id,
                        event_id=review.event_id,
                        work_id=review.work_id,
                        submission_id=review.submission_id,
                        reviewer_id=review.reviewer_id,
                        status=review.status,
                        review=review.review,
                        creation_date=review.creation_date,
                        last_update=review.last_update,
                        reviewer={
                            "name": review.reviewer.name,
                            "lastname": review.reviewer.lastname,
                            "email": review.reviewer.email,
                        },
                    )
                    for review in row.work.reviews
                    if review.reviewer_id == user_id
                ],
            )
            for row in res
        ]
