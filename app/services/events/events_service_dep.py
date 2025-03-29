from typing import Annotated

from fastapi import Depends

from app.repository.events_repository import EventsRepository
from app.repository.repository import get_repository
from app.services.event_organizers.event_organizers_service_dep import EventOrganizersServiceDep
from app.services.events.events_service import EventsService
from app.services.notifications.notifications_service_dep import EventsNotificationServiceDep


class EventsChecker:
    async def __call__(
        self,
        event_notification_service: EventsNotificationServiceDep,
        organizers_service: EventOrganizersServiceDep,
        events_repository: EventsRepository = Depends(get_repository(EventsRepository)),
    ) -> EventsService:
        return EventsService(events_repository, organizers_service, event_notification_service)


events_checker = EventsChecker()
EventsServiceDep = Annotated[EventsService, Depends(events_checker)]
