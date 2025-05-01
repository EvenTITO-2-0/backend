from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Query

from app.authorization.caller_id_dep import CallerIdDep
from app.services.event_chairs.event_chairs_service_dep import EventChairServiceDep
from app.services.works.works_service_dep import WorksServiceDep


class IsChair:
    async def __call__(self, caller_id: CallerIdDep, chair_service: EventChairServiceDep) -> bool:
        return await chair_service.is_chair(caller_id)


IsChairDep = Annotated[bool, Depends(IsChair())]


class VerifyIsChair:
    async def __call__(self, is_event_chair: IsChairDep) -> None:
        if not is_event_chair:
            raise HTTPException(status_code=403)


ChairDep = Annotated[None, Depends(VerifyIsChair())]


class IsTrackChair:
    async def __call__(
        self, caller_id: CallerIdDep, chair_service: EventChairServiceDep, track: str | None = Query(default=None)
    ) -> bool:
        if await chair_service.is_chair(caller_id):
            chair = await chair_service.get_chair(caller_id)
            return track in chair.tracks
        return False


IsTrackChairDep = Annotated[bool, Depends(IsTrackChair())]


class VerifyIsTrackChair:
    async def __call__(self, is_event_track_chair: IsTrackChairDep) -> None:
        if not is_event_track_chair:
            raise HTTPException(status_code=403)


verify_is_track_chair = VerifyIsTrackChair()
TrackChairDep = Annotated[None, Depends(verify_is_track_chair)]


class IsWorkChair:
    async def __call__(
        self,
        caller_id: CallerIdDep,
        chair_service: EventChairServiceDep,
        work_service: WorksServiceDep,
        work_id: UUID | Optional[UUID] | None = None,
    ) -> bool:
        if (work_id is not None) and (await chair_service.is_chair(caller_id)):
            chair = await chair_service.get_chair(caller_id)
            work = await work_service.get_work(work_id)
            return work.track in chair.tracks
        return False


IsWorkChairDep = Annotated[bool, Depends(IsWorkChair())]


class VerifyIsWorkChair:
    async def __call__(self, is_event_work_chair: IsWorkChairDep) -> None:
        if not is_event_work_chair:
            raise HTTPException(status_code=403)


verify_is_work_chair = VerifyIsWorkChair()
WorkChairDep = Annotated[None, Depends(verify_is_work_chair)]
