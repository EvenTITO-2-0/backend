from fastapi import APIRouter

from app.authorization.util_dep import or_
from app.services.events.events_administration_service_dep import EventsAdministrationServiceDep

from ...authorization.admin_user_dep import IsAdminUsrDep
from ...authorization.organizer_dep import IsOrganizerDep
from ...authorization.user_id_dep import UserDep
from ...schemas.events.event_status import EventStatusSchema

events_admin_router = APIRouter(prefix="/{event_id}", tags=["Events: Administration"])


@events_admin_router.patch(
    path="/status", status_code=204, response_model=None, dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def change_event_status(
    service: EventsAdministrationServiceDep, status_modification: EventStatusSchema, user_role: UserDep
):
    await service.update_status(status_modification, user_role)
