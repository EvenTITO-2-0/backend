from logging import getLogger
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.review import ReviewModel
from app.database.models.submission import SubmissionModel
from app.database.models.work import WorkModel
from app.repository.crud_repository import Repository
from app.schemas.users.user import PublicUserSchema
from app.schemas.users.utils import UID
from app.schemas.works.review import ReviewCreateRequestSchema, ReviewPublishSchema, ReviewResponseSchema

logger = getLogger(__name__)


class ReviewsRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ReviewModel)

    async def get_all_work_reviews_for_event(
        self, event_id: UUID, work_id: UUID, offset: int, limit: int
    ) -> list[ReviewResponseSchema]:
        return await self._get_work_reviews(
            [ReviewModel.event_id == event_id, ReviewModel.work_id == work_id], offset, limit
        )

    async def get_shared_work_reviews(
        self, event_id: UUID, work_id: UUID, offset: int, limit: int
    ) -> list[ReviewResponseSchema]:
        return await self._get_work_reviews(
            [ReviewModel.event_id == event_id, ReviewModel.work_id == work_id, ReviewModel.shared.is_(True)],
            offset,
            limit,
        )

    async def exists_review(self, event_id: UUID, work_id: UUID, reviewer_id: UID, submission_id: UUID) -> bool:
        conditions = [
            ReviewModel.event_id == event_id,
            ReviewModel.work_id == work_id,
            ReviewModel.submission_id == submission_id,
            ReviewModel.reviewer_id == reviewer_id,
        ]
        return await self._exists_with_conditions(conditions)

    async def create_review(
        self,
        event_id: UUID,
        work_id: UUID,
        reviewer_id: UID,
        submission_id: UUID,
        review_schema: ReviewCreateRequestSchema,
    ) -> ReviewResponseSchema:
        new_review = ReviewModel(
            **review_schema.model_dump(),
            event_id=event_id,
            work_id=work_id,
            reviewer_id=reviewer_id,
            submission_id=submission_id,
        )
        saved_review = await self._create(new_review)
        return ReviewResponseSchema(
            id=saved_review.id,
            event_id=saved_review.event_id,
            work_id=saved_review.work_id,
            submission_id=saved_review.submission_id,
            reviewer_id=saved_review.reviewer_id,
            review=saved_review.review,
            status=saved_review.status,
            creation_date=saved_review.creation_date,
            last_update=saved_review.last_update,
            reviewer=PublicUserSchema(
                email=saved_review.reviewer.email,
                name=saved_review.reviewer.name,
                lastname=saved_review.reviewer.lastname,
            ),
        )

    async def update_review(self, review_id: UUID, review_update: ReviewCreateRequestSchema) -> bool:
        conditions = [ReviewModel.id == review_id]
        return await self._update_with_conditions(conditions, review_update)

    async def publish_reviews(self, event_id: UUID, work_id: UUID, reviews_to_publish: ReviewPublishSchema) -> bool:
        logger.info("Publishing reviews for work %s in event %s", work_id, event_id)
        reviews_ids = reviews_to_publish.reviews_to_publish
        if len(reviews_ids) == 0:
            logger.error("No reviews to publish provided")
            return False

        work_num = await self.get_max_work_number_for_event(event_id)
        logger.info(f"Publishing reviews with work number {work_num}")
        update_work_query = (
            update(WorkModel)
            .where(and_(WorkModel.event_id == event_id, WorkModel.id == work_id))
            .values(state=reviews_to_publish.new_work_status, work_number=work_num + 1)
        )
        if reviews_to_publish.resend_deadline is not None:
            logger.info("Setting new resend deadline for work %s in event %s", work_id, event_id)
            update_work_query.values(deadline_date=reviews_to_publish.resend_deadline)

        for review_id in reviews_ids:
            conditions = [ReviewModel.event_id == event_id, ReviewModel.work_id == work_id, ReviewModel.id == review_id]
            review = await self._get_with_conditions(conditions)
            if not review:
                logger.error(
                    "Couldnt obtain review %s to publish for work %s in event %s", review_id, work_id, event_id
                )
                return False

            update_review_query = update(ReviewModel).where(ReviewModel.id == review.id).values(shared=True)
            update_submission_query = (
                update(SubmissionModel)
                .where(SubmissionModel.id == review.submission_id)
                .values(state=reviews_to_publish.new_work_status)
            )
            await self.session.execute(update_review_query)
            await self.session.execute(update_submission_query)
        await self.session.execute(update_work_query)
        await self.session.commit()
        logger.info("Successfully published reviews for work %s in event %s", work_id, event_id)
        return True

    async def _get_work_reviews(self, conditions, offset: int, limit: int) -> list[ReviewResponseSchema]:
        res = await self._get_many_with_conditions(conditions, offset, limit)
        return [
            ReviewResponseSchema(
                id=row.id,
                event_id=row.event_id,
                work_id=row.work_id,
                submission_id=row.submission_id,
                reviewer_id=row.reviewer_id,
                status=row.status,
                review=row.review,
                shared=row.shared,
                creation_date=row.creation_date,
                last_update=row.last_update,
                reviewer=PublicUserSchema(
                    email=row.reviewer.email, name=row.reviewer.name, lastname=row.reviewer.lastname
                ),
            )
            for row in res
        ]

    async def get_max_work_number_for_event(self, event_id: UUID) -> int:
        """
        Return the highest work_number for a given event_id, or 0 if none exist.
        Works correctly with an AsyncSession.
        """
        stmt = select(func.coalesce(func.max(WorkModel.work_number), 0)).where(WorkModel.event_id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()
