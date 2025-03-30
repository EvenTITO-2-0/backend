from uuid import UUID

from app.database.models.event import EventStatus
from app.database.models.user import UserRole
from app.exceptions.events_exceptions import EventNotFound, InvalidCaller, InvalidEventConfiguration
from app.repository.events_repository import EventsRepository
from app.schemas.events.event_status import EventStatusSchema
from app.services.notifications.events_notifications_service import EventsNotificationsService
from app.services.services import BaseService


class EventsAdministrationService(BaseService):
    def __init__(
        self, event_id: UUID, events_repository: EventsRepository, notification_service: EventsNotificationsService
    ):
        self.event_id = event_id
        self.events_repository = events_repository
        self.notification_service = notification_service

    async def update_status(self, new_status: EventStatusSchema, caller_role: UserRole):
        event = await self.events_repository.get(self.event_id)
        admin_status = [EventStatus.WAITING_APPROVAL, EventStatus.NOT_APPROVED, EventStatus.BLOCKED]
        if (caller_role != UserRole.ADMIN) and (event.status in admin_status or new_status.status in admin_status):
            raise InvalidCaller()

        # Check change STARTED status(publish event)
        if new_status.status == EventStatus.STARTED and not self.__all_mandatory_config_ok(event):
            raise InvalidEventConfiguration()

        update_ok = await self.events_repository.update(self.event_id, new_status)
        if not update_ok:
            raise EventNotFound(self.event_id)

        await self.__notify_change(new_status, event)

    def __all_mandatory_config_ok(self, event) -> bool:
        return True
        # TODO: HOTFIX to accept everything. This should not happen!
        # event_dates = DatesCompleteSchema.model_validate(event)
        # for date in event_dates.dates:
        #     if date.date is None and date.time is None:
        #         return False
        # return True

    async def __notify_change(self, new_status, event):
        if new_status.status.value == EventStatus.CREATED.value:
            await self.notification_service.notify_event_created(event)
        elif new_status.status.value == EventStatus.STARTED.value:
            await self.notification_service.notify_event_started(event)
