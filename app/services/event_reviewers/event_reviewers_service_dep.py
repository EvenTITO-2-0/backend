from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.repository.repository import get_repository
from app.repository.reviewers_repository import ReviewerRepository
from app.repository.users_repository import UsersRepository
from app.services.event_reviewers.event_reviewers_service import EventReviewerService
from app.services.events.events_service_dep import EventsServiceDep
from app.services.notifications.notifications_service_dep import EventsNotificationServiceDep
from app.services.works.works_service_dep import WorksServiceDep


class EventsReviewerChecker:
    async def __call__(
        self,
        event_id: UUID,
        event_notification_service: EventsNotificationServiceDep,
        events_service: EventsServiceDep,
        work_service: WorksServiceDep,
        users_repository: UsersRepository = Depends(get_repository(UsersRepository)),
        reviewer_repository: ReviewerRepository = Depends(get_repository(ReviewerRepository)),
    ) -> EventReviewerService:
        return EventReviewerService(
            event_id, events_service, work_service, reviewer_repository, users_repository, event_notification_service
        )


event_reviewer_checker = EventsReviewerChecker()
EventReviewerServiceDep = Annotated[EventReviewerService, Depends(event_reviewer_checker)]
