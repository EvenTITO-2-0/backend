from typing import Annotated

from fastapi import BackgroundTasks, Depends

from app.repository.events_repository import EventsRepository
from app.repository.organizers_repository import OrganizerRepository
from app.repository.repository import get_repository
from app.repository.users_repository import UsersRepository
from app.services.notifications.events_notifications_service import EventsNotificationsService


class EventsNotification:
    async def __call__(
        self,
        background_tasks: BackgroundTasks,
        events_repository: EventsRepository = Depends(get_repository(EventsRepository)),
        users_repository: UsersRepository = Depends(get_repository(UsersRepository)),
        organizer_repository: OrganizerRepository = Depends(get_repository(OrganizerRepository)),
    ) -> EventsNotificationsService:
        return EventsNotificationsService(events_repository, users_repository, organizer_repository, background_tasks)


events_notification_service = EventsNotification()
EventsNotificationServiceDep = Annotated[EventsNotificationsService, Depends(events_notification_service)]
