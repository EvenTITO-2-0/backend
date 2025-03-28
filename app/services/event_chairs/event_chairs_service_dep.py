from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.repository.chairs_repository import ChairRepository
from app.repository.repository import get_repository
from app.repository.users_repository import UsersRepository
from app.services.event_chairs.event_chairs_service import EventChairService
from app.services.events.events_configuration_service_dep import EventsConfigurationServiceDep


class EventsChairChecker:
    async def __call__(
        self,
        event_id: UUID,
        event_configuration_service: EventsConfigurationServiceDep,
        users_repository: Annotated[UsersRepository, Depends(get_repository(UsersRepository))],
        chair_repository: Annotated[ChairRepository, Depends(get_repository(ChairRepository))],
    ) -> EventChairService:
        return EventChairService(event_id, event_configuration_service, chair_repository, users_repository)


event_chair_checker = EventsChairChecker()
EventChairServiceDep = Annotated[EventChairService, Depends(event_chair_checker)]
