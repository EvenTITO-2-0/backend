import logging

from fastapi import APIRouter

import time
from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.chair_dep import IsChairDep
from app.authorization.util_dep import or_
from app.routers.events.configuration.dates import dates_configuration_router
from app.routers.events.configuration.general import general_configuration_router
from app.routers.events.configuration.pricing import pricing_configuration_router
from app.routers.events.configuration.review_skeleton import review_skeleton_configuration_router
from app.schemas.events.configuration import EventConfigurationSchema
from app.services.events.events_configuration_service_dep import EventsConfigurationServiceDep
from app.services.slots.slots_configuration_service_dep import SlotsConfigurationServiceDep

events_configuration_router = APIRouter(prefix="/{event_id}/configuration", tags=["Events: Configuration"])

events_configuration_router.include_router(dates_configuration_router)
events_configuration_router.include_router(general_configuration_router)
events_configuration_router.include_router(pricing_configuration_router)
events_configuration_router.include_router(review_skeleton_configuration_router)
logger = logging.getLogger(__name__)

@events_configuration_router.get("", dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)])
async def get_event_configuration(events_configuration_service: EventsConfigurationServiceDep,) -> EventConfigurationSchema:
    logger.info(f"Fetching configuration for event {events_configuration_service.event_id}")
    event = await events_configuration_service.get_configuration()
    return event


@events_configuration_router.get(path="/slots", status_code=201)
async def create_event_slots(slots_configuration_service: SlotsConfigurationServiceDep,) -> None:
    logger.info(f"Starting slot and room configuration for event {slots_configuration_service.event_id}")
    await slots_configuration_service.configure_event_slots_and_rooms()
    time.sleep(2)
    return