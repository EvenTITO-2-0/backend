from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.repository.organizers_repository import OrganizerRepository
from app.repository.repository import get_repository
from app.repository.users_repository import UsersRepository
from app.services.event_organizers.event_organizers_service import EventOrganizersService


class EventsOrganizerChecker:
    async def __call__(
        self,
        users_repository: Annotated[UsersRepository, Depends(get_repository(UsersRepository))],
        organizers_repository: Annotated[OrganizerRepository, Depends(get_repository(OrganizerRepository))],
        event_id: UUID | None = None,
    ) -> EventOrganizersService:
        return EventOrganizersService(event_id, organizers_repository, users_repository)


event_organizers_checker = EventsOrganizerChecker()
EventOrganizersServiceDep = Annotated[EventOrganizersService, Depends(event_organizers_checker)]
