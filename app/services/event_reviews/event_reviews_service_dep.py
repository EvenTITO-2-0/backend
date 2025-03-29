from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.authorization.caller_id_dep import CallerIdDep
from app.repository.repository import get_repository
from app.repository.reviews_repository import ReviewsRepository
from app.services.event_reviews.event_reviews_service import EventReviewsService
from app.services.event_submissions.event_submissions_service_dep import SubmissionsServiceDep
from app.services.storage.work_storage_service_dep import WorkStorageServiceDep
from app.services.works.works_service_dep import WorksServiceDep


class EventReviewsServiceChecker:
    async def __call__(
        self,
        event_id: UUID,
        work_id: UUID,
        caller_id: CallerIdDep,
        work_service: WorksServiceDep,
        submission_service: SubmissionsServiceDep,
        storage_service: WorkStorageServiceDep,
        reviews_repository: Annotated[ReviewsRepository, Depends(get_repository(ReviewsRepository))],
    ) -> EventReviewsService:
        return EventReviewsService(
            event_id, work_id, caller_id, work_service, submission_service, storage_service, reviews_repository
        )


event_reviews_checker = EventReviewsServiceChecker()
EventReviewsServiceDep = Annotated[EventReviewsService, Depends(event_reviews_checker)]
