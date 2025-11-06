from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.author_dep import IsAuthorDep, verify_is_author
from app.authorization.chair_dep import IsTrackChairDep, IsWorkChairDep
from app.authorization.organizer_dep import IsOrganizerDep, verify_is_organizer
from app.authorization.reviewer_dep import IsWorkReviewerDep
from app.authorization.user_id_dep import verify_user_exists
from app.authorization.util_dep import or_
from app.schemas.works.work import (
    CreateWorkSchema,
    WorkStateSchema,
    WorkUpdateAdministrationSchema,
    WorkUpdateSchema,
    WorkWithState,
)
from app.services.works.works_service_dep import WorksServiceDep

works_router = APIRouter(prefix="/{event_id}/works", tags=["Events: Works"])

@works_router.get(
    path="", status_code=200, response_model=List[WorkWithState], dependencies=[or_(IsOrganizerDep, IsTrackChairDep)]
)
async def get_works(
    work_service: WorksServiceDep,
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    track: str = Query(default=None),
) -> list[WorkWithState]:
    return await work_service.get_works(track, offset, limit)

@works_router.get(path="/unassigned", status_code=200, dependencies=[or_(IsAdminUsrDep, IsOrganizerDep)])
async def get_unassigned_works(
    works_service: WorksServiceDep,
) -> list[WorkWithState]:
    unassigned_works = await works_service.get_unassigned_works()
    return unassigned_works

@works_router.get(
    path="/talks", status_code=200, response_model=List[WorkWithState], dependencies=[Depends(verify_user_exists)]
)
async def get_works_with_talk_not_null(
    work_service: WorksServiceDep, offset: int = 0, limit: int = Query(default=100, le=100)
) -> list[WorkWithState]:
    return await work_service.get_works_with_talk_not_null(offset, limit)


@works_router.get(
    path="/my-works", status_code=200, response_model=List[WorkWithState], dependencies=[Depends(verify_user_exists)]
)
async def read_my_works(
    work_service: WorksServiceDep, offset: int = 0, limit: int = Query(default=100, le=100)
) -> list[WorkWithState]:
    return await work_service.get_my_works(offset, limit)


@works_router.get(
    path="/{work_id}",
    status_code=200,
    response_model=WorkWithState,
    dependencies=[or_(IsOrganizerDep, IsAuthorDep, IsWorkChairDep, IsWorkReviewerDep)],
)
async def get_work(work_id: UUID, work_service: WorksServiceDep) -> WorkWithState:
    return await work_service.get_work(work_id)


@works_router.post(path="", status_code=201, dependencies=[Depends(verify_user_exists)])
async def create_work(work: CreateWorkSchema, work_service: WorksServiceDep) -> UUID:
    return await work_service.create_work(work)


@works_router.put(path="/{work_id}", status_code=204, dependencies=[Depends(verify_is_author)])
async def update_work(work_id: UUID, work_update: WorkUpdateSchema, work_service: WorksServiceDep) -> None:
    await work_service.update_work(work_id, work_update)


@works_router.put(path="/{work_id}/administration", status_code=204, dependencies=[Depends(verify_is_organizer)])
async def update_work_administration(
    work_id: UUID, work_update: WorkUpdateAdministrationSchema, work_service: WorksServiceDep
) -> None:
    await work_service.update_work_administration(work_id, work_update)


@works_router.patch(path="/{work_id}/status", status_code=204, dependencies=[or_(IsAdminUsrDep, IsOrganizerDep)])
async def update_work_status(work_id: UUID, status: WorkStateSchema, work_service: WorksServiceDep) -> None:
    await work_service.update_work_status(work_id, status)
