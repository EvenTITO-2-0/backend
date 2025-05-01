from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.repository.events_repository import EventsRepository
from app.repository.repository import get_repository
from app.services.events.events_administration_service import EventsAdministrationService
from app.services.notifications.notifications_service_dep import EventsNotificationServiceDep


class EventsAdministrationServiceChecker:
    async def __call__(
        self,
        event_id: UUID,
        events_notifications_service: EventsNotificationServiceDep,
        events_repository: Annotated[EventsRepository, Depends(get_repository(EventsRepository))],
    ) -> EventsAdministrationService:
        return EventsAdministrationService(event_id, events_repository, events_notifications_service)


events_administrations_checker = EventsAdministrationServiceChecker()
EventsAdministrationServiceDep = Annotated[EventsAdministrationService, Depends(events_administrations_checker)]
