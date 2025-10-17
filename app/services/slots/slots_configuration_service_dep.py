from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.repository.events_repository import EventsRepository
from app.repository.slots_repository import SlotsRepository
from app.repository.repository import get_repository
from app.services.slots.slots_configuration_service import SlotsConfigurationService


class SlotsConfigurationChecker:
    async def __call__(
        self,
        event_id: UUID,
        events_repository: Annotated[EventsRepository, Depends(get_repository(EventsRepository))],
        slots_repository: Annotated[SlotsRepository, Depends(get_repository(SlotsRepository))],
    ) -> SlotsConfigurationService:
        return SlotsConfigurationService(event_id, events_repository, slots_repository)


slots_configuration_checker = SlotsConfigurationChecker()
SlotsConfigurationServiceDep = Annotated[SlotsConfigurationService, Depends(slots_configuration_checker)]
