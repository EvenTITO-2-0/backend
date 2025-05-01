from typing import List

from fastapi import APIRouter

from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.caller_id_dep import CallerIdDep
from app.authorization.chair_dep import IsChairDep
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.util_dep import or_
from app.schemas.events.schemas import DynamicTracksEventSchema
from app.schemas.members.chair_schema import ChairResponseSchema
from app.schemas.users.utils import UID
from app.services.event_chairs.event_chairs_service_dep import EventChairServiceDep

event_chairs_router = APIRouter(prefix="/{event_id}/chairs", tags=["Events: Chairs"])


@event_chairs_router.get(
    path="", response_model=List[ChairResponseSchema], dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def read_event_chairs(chair_service: EventChairServiceDep) -> List[ChairResponseSchema]:
    return await chair_service.get_all_chairs()


@event_chairs_router.get(path="/me", response_model=ChairResponseSchema, dependencies=[or_(IsOrganizerDep, IsChairDep)])
async def get_my_chair(caller_id: CallerIdDep, chair_service: EventChairServiceDep) -> ChairResponseSchema:
    return await chair_service.get_chair(caller_id)


@event_chairs_router.get(
    path="/{user_id}", response_model=ChairResponseSchema, dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def get_chair(user_id: UID, chair_service: EventChairServiceDep) -> ChairResponseSchema:
    return await chair_service.get_chair(user_id)


@event_chairs_router.delete(
    path="/{user_id}", status_code=204, response_model=None, dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def remove_chair(user_id: UID, chair_service: EventChairServiceDep) -> None:
    await chair_service.remove_chair(user_id)


@event_chairs_router.put(
    path="/{user_id}/tracks", status_code=204, response_model=None, dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def update(user_id: UID, tracks: DynamicTracksEventSchema, chair_service: EventChairServiceDep) -> None:
    await chair_service.update_tracks(user_id, tracks)
