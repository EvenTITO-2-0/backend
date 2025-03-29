from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.repository.events_repository import EventsRepository
from app.repository.repository import get_repository
from app.services.events.events_configuration_service import EventsConfigurationService


class EventsConfigurationChecker:
    async def __call__(
        self,
        event_id: UUID,
        events_repository: EventsRepository = Depends(get_repository(EventsRepository)),
    ) -> EventsConfigurationService:
        return EventsConfigurationService(event_id, events_repository)


events_configuration_checker = EventsConfigurationChecker()
EventsConfigurationServiceDep = Annotated[EventsConfigurationService, Depends(events_configuration_checker)]
