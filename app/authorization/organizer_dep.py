from typing import Annotated

from fastapi import Depends, HTTPException

from app.authorization.caller_id_dep import CallerIdDep
from app.services.event_organizers.event_organizers_service_dep import EventOrganizersServiceDep


class IsOrganizer:
    async def __call__(self, caller_id: CallerIdDep, organizers_service: EventOrganizersServiceDep) -> bool:
        return await organizers_service.is_organizer(caller_id)


IsOrganizerDep = Annotated[bool, Depends(IsOrganizer())]


class VerifyIsOrganizer:
    async def __call__(self, is_event_organizer: IsOrganizerDep) -> None:
        if not is_event_organizer:
            raise HTTPException(status_code=403)


verify_is_organizer = VerifyIsOrganizer()
OrganizerDep = Annotated[None, Depends(verify_is_organizer)]
