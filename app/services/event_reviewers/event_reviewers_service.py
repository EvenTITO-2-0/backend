from uuid import UUID

from app.exceptions.members.reviewer.reviewer_exceptions import AlreadyReviewerExist, UserNotIsReviewer
from app.exceptions.users_exceptions import UserNotFound
from app.exceptions.works.works_exceptions import WorkNotFound
from app.repository.reviewers_repository import ReviewerRepository
from app.repository.users_repository import UsersRepository
from app.schemas.members.reviewer_schema import (
    ReviewerAssignmentWithWorkSchema,
    ReviewerCreateRequestSchema,
    ReviewerResponseSchema,
    ReviewerUpdateRequestSchema,
    ReviewerWithWorksDeadlineResponseSchema,
    ReviewerWithWorksResponseSchema,
)
from app.schemas.users.utils import UID
from app.services.events.events_service import EventsService
from app.services.notifications.events_notifications_service import EventsNotificationsService
from app.services.services import BaseService
from app.services.works.works_service import WorksService


class EventReviewerService(BaseService):
    def __init__(
        self,
        event_id: UUID,
        event_service: EventsService,
        work_service: WorksService,
        reviewer_repository: ReviewerRepository,
        users_repository: UsersRepository,
        event_notification_service: EventsNotificationsService,
    ):
        self.event_id = event_id
        self.event_service = event_service
        self.work_service = work_service
        self.reviewer_repository = reviewer_repository
        self.users_repository = users_repository
        self.event_notification_service = event_notification_service

    async def is_reviewer_in_event(self, user_id: UID) -> bool:
        return await self.reviewer_repository.is_reviewer_in_event(self.event_id, user_id)

    async def is_reviewer_of_work_in_event(self, user_id: UID, work_id: UUID) -> bool:
        return await self.reviewer_repository.is_reviewer_of_work_in_event(self.event_id, user_id, work_id)

    async def get_reviewers(self, work_id: UUID | None) -> list[ReviewerWithWorksDeadlineResponseSchema]:
        return await self.reviewer_repository.get_all_reviewers(self.event_id, work_id)

    async def get_reviewer_by_user_id(self, user_id: UID) -> ReviewerWithWorksResponseSchema:
        if not await self.is_reviewer_in_event(user_id):
            raise UserNotIsReviewer(self.event_id, user_id)
        return await self.reviewer_repository.get_reviewer_by_user_id(self.event_id, user_id)

    async def get_reviewer_by_user_id_and_work_id(self, user_id: UID, work_id: UUID) -> ReviewerResponseSchema:
        if not await self.is_reviewer_of_work_in_event(user_id, work_id):
            raise UserNotIsReviewer(self.event_id, user_id)
        return await self.reviewer_repository.get_reviewer_by_work_id(self.event_id, user_id, work_id)

    async def add_reviewers(self, create_schema: ReviewerCreateRequestSchema) -> None:
        for new_reviewer in create_schema.reviewers:
            user_id = await self.users_repository.get_user_id_by_email(new_reviewer.email)
            if user_id is None:
                raise UserNotFound(new_reviewer.email)
            if not await self.work_service.exist_work(new_reviewer.work_id):
                raise WorkNotFound(self.event_id, new_reviewer.work_id)
            if await self.is_reviewer_of_work_in_event(user_id, new_reviewer.work_id):
                raise AlreadyReviewerExist(self.event_id, user_id, new_reviewer.work_id)
            new_reviewer._user_id = user_id
        await self.reviewer_repository.create_reviewers(self.event_id, create_schema.reviewers)
        # Sending notification email
        await self.event_notification_service.notify_new_reviewers(self.event_id, create_schema)

    async def update_reviewer(self, update_schema: ReviewerUpdateRequestSchema) -> None:
        if not await self.work_service.exist_work(update_schema.work_id):
            raise WorkNotFound(self.event_id, update_schema.work_id)
        if not await self.is_reviewer_of_work_in_event(update_schema.user_id, update_schema.work_id):
            raise UserNotIsReviewer(self.event_id, update_schema.user_id)
        await self.reviewer_repository.update_reviewer(self.event_id, update_schema)

    async def get_my_assignments(self, user_id: UID) -> list[ReviewerAssignmentWithWorkSchema]:
        return await self.reviewer_repository.get_assignments(self.event_id, user_id)
