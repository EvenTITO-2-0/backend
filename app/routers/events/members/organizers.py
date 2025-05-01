from typing import List

from fastapi import APIRouter

from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.util_dep import or_
from app.schemas.members.member_schema import MemberResponseSchema
from app.schemas.users.utils import UID
from app.services.event_organizers.event_organizers_service_dep import EventOrganizersServiceDep

event_organizers_router = APIRouter(prefix="/{event_id}/organizers", tags=["Events: Organizers"])


@event_organizers_router.get(
    path="", response_model=List[MemberResponseSchema], dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def read_event_organizers(organizer_service: EventOrganizersServiceDep):
    return await organizer_service.get_all_organizers()


@event_organizers_router.delete(
    path="/{user_id}", status_code=201, response_model=None, dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def remove_organizer(user_id: UID, organizer_service: EventOrganizersServiceDep) -> None:
    await organizer_service.remove_organizer(user_id)
