import logging

from fastapi import APIRouter

import time
from typing import List

from sqlalchemy import UUID

from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.util_dep import or_
from app.routers.events.configuration.dates import dates_configuration_router
from app.routers.events.configuration.general import general_configuration_router
from app.routers.events.configuration.pricing import pricing_configuration_router
from app.routers.events.configuration.review_skeleton import review_skeleton_configuration_router
from app.schemas.events.assing_works_parameters import AssignWorksParametersSchema
from app.schemas.events.configuration import EventConfigurationSchema
from app.schemas.events.slot_with_works import SlotWithWorksSchema
from app.services.events.events_configuration_service_dep import EventsConfigurationServiceDep
from app.services.slots.slots_configuration_service_dep import SlotsConfigurationServiceDep
from app.schemas.events.slot import SlotSchema

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

@events_configuration_router.delete(path="/slots", status_code=200)
async def delete_event_slots(slots_configuration_service: SlotsConfigurationServiceDep,) -> None:
    logger.info(f"Deleting slot and room configuration for event {slots_configuration_service.event_id}")
    await slots_configuration_service.delete_event_slots_and_rooms()
    return

@events_configuration_router.delete(path="/slots/{slot_id}", status_code=200)
async def delete_event_slot(slot_id: int, slots_configuration_service: SlotsConfigurationServiceDep,) -> None:
    logger.info(f"Deleting slot {slot_id} for event {slots_configuration_service.event_id}")
    await slots_configuration_service.delete_event_slot(slot_id)
    return

@events_configuration_router.post(path="/slots", status_code=201)
async def create_event_slot(new_slot: SlotSchema, slots_configuration_service: SlotsConfigurationServiceDep,) -> None:
    logger.info(f"Creating slot and room configuration for event {slots_configuration_service.event_id}")
    await slots_configuration_service.create_event_slot(new_slot)
    return

@events_configuration_router.put(path="/slots/{slot_id}", status_code=200)
async def update_event_slot(slot_id: int, new_slot: SlotSchema, slots_configuration_service: SlotsConfigurationServiceDep,) -> None:
    logger.info(f"Updating slot {slot_id} for event {slots_configuration_service.event_id}")
    await slots_configuration_service.update_event_slot(slot_id, new_slot)
    return

@events_configuration_router.post(path="/slots/assign", status_code=200)
async def assign_works_to_slots(parameters: AssignWorksParametersSchema, slots_configuration_service: SlotsConfigurationServiceDep,) -> None:
    logger.info(f"Assigning works to slots for event {slots_configuration_service.event_id}")
    await slots_configuration_service.assign_works_to_slots(parameters)
    time.sleep(1)
    return

@events_configuration_router.get(path="/slots/works", status_code=200)
async def get_slots_with_works(slots_configuration_service: SlotsConfigurationServiceDep,) -> List[SlotWithWorksSchema]:
    logger.info(f"Fetching slots with works for event {slots_configuration_service.event_id}")
    slots = await slots_configuration_service.get_slots_with_works()
    return slots

@events_configuration_router.delete(path="/slots/works/{work_id}", status_code=200)
async def delete_work_for_slot(work_id: str, slots_configuration_service: SlotsConfigurationServiceDep,) -> None:
    logger.info(f"Fetching slots with works for event {slots_configuration_service.event_id}")
    await slots_configuration_service.delete_slot_work(work_id)
    return


