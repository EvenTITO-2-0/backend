from fastapi import APIRouter

from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.util_dep import or_
from app.schemas.events.dates import DatesCompleteSchema
from app.services.events.events_configuration_service_dep import EventsConfigurationServiceDep

dates_configuration_router = APIRouter(prefix="/dates")


@dates_configuration_router.put(
    path="", status_code=204, response_model=None, dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def update_dates_event(
    dates_modification: DatesCompleteSchema,
    events_configuration_service: EventsConfigurationServiceDep,
):
    await events_configuration_service.update_dates(dates_modification)
