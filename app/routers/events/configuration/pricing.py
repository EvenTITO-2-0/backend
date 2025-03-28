from fastapi import APIRouter

from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.util_dep import or_
from app.schemas.events.schemas import PricingSchema
from app.services.events.events_configuration_service_dep import EventsConfigurationServiceDep

pricing_configuration_router = APIRouter(prefix="/pricing")


@pricing_configuration_router.put(
    path="", status_code=204, response_model=None, dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def update_pricing_event(
    pricing_modification: PricingSchema,
    events_configuration_service: EventsConfigurationServiceDep,
):
    await events_configuration_service.update_pricing(pricing_modification)
