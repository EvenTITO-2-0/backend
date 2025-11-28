import time
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import WorkSlotModel
from app.database.models.work import WorkModel, WorkStates
from app.repository.crud_repository import Repository
from app.schemas.users.utils import UID
from app.schemas.works.work import (
    CompleteWork,
    CreateWorkSchema,
    WorkStateSchema,
    WorkUpdateAdministrationSchema,
    WorkUpdateSchema,
)


class WorksRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkModel)

    async def get_work(self, event_id: UUID, work_id: UUID) -> CompleteWork:
        conditions = [WorkModel.event_id == event_id, WorkModel.id == work_id]
        work = await self._get_with_conditions(conditions)
        return work

    async def get_all_works_with_talk_not_null(self, event_id: UUID, offset: int, limit: int) -> list[WorkModel]:
        conditions = [WorkModel.event_id == event_id, WorkModel.talk.is_not(None)]
        return await self._get_many_with_conditions(conditions, offset, limit)

    async def get_all_works_for_event(self, event_id: UUID, offset: int, limit: int) -> list[WorkModel]:
        # Custom query with Eager Loading to avoid MissingGreenlet error
        stmt = (
            select(WorkModel)
            .where(WorkModel.event_id == event_id)
            .options(selectinload(WorkModel.slot_links).selectinload(WorkSlotModel.slot))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_works_by_track(self, event_id: UUID, track: str, offset: int, limit: int) -> list[WorkModel]:
        # Custom query with Eager Loading
        stmt = (
            select(WorkModel)
            .where(WorkModel.event_id == event_id, WorkModel.track == track)
            .options(selectinload(WorkModel.slot_links).selectinload(WorkSlotModel.slot))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_works_for_user_in_event(
        self, event_id: UUID, user_id: UID, offset: int, limit: int
    ) -> list[WorkModel]:
        conditions = [WorkModel.author_id == user_id, WorkModel.event_id == event_id]
        return await self._get_many_with_conditions(conditions, offset, limit)

    async def get_works_in_tracks(self, event_id: UUID, tracks: list[str], offset: int, limit: int) -> list[WorkModel]:
        conditions = [WorkModel.event_id == event_id, WorkModel.track.in_(tracks)]
        return await self._get_many_with_conditions(conditions, offset, limit)

    async def create_work(self, work: CreateWorkSchema, event_id: UUID, deadline_date: datetime, author_id: UID):
        work_model = WorkModel(**work.model_dump(), event_id=event_id, deadline_date=deadline_date, author_id=author_id)
        return await self._create(work_model)

    async def update_work(self, work_update: WorkUpdateSchema, event_id: UUID, work_id: UUID) -> bool:
        conditions = [WorkModel.event_id == event_id, WorkModel.id == work_id]
        return await self._update_with_conditions(conditions, work_update)

    async def update_work_administration(
        self, work_update: WorkUpdateAdministrationSchema, event_id: UUID, work_id: UUID
    ) -> bool:
        conditions = [WorkModel.event_id == event_id, WorkModel.id == work_id]
        return await self._update_with_conditions(conditions, work_update)

    async def work_with_title_exists(self, event_id: UUID, title: str):
        conditions = [WorkModel.event_id == event_id, WorkModel.title == title]
        return await self._exists_with_conditions(conditions)

    async def exists_work(self, event_id: UUID, work_id: UUID) -> bool:
        conditions = [WorkModel.event_id == event_id, WorkModel.id == work_id]
        return await self._exists_with_conditions(conditions)

    async def update_work_status(self, event_id: UUID, work_id: UUID, status: WorkStateSchema):
        conditions = [WorkModel.event_id == event_id, WorkModel.id == work_id]
        return await self._update_with_conditions(conditions, status)

    async def get_all_approved_works_for_event(self, event_id: UUID, offset: int, limit: int) -> list[WorkModel]:
        conditions = [WorkModel.event_id == event_id, WorkModel.state == WorkStates.APPROVED]
        return await self._get_many_with_conditions(conditions, offset, limit)

    async def get_unassigned_works(self, event_id: UUID, offset: int, limit: int) -> list[WorkModel]:
        conditions = [
            WorkModel.event_id == event_id,
            WorkModel.state == WorkStates.APPROVED,
            ~WorkModel.slot_links.any(),  # No related slot links
        ]
        return await self._get_many_with_conditions(conditions, offset, limit)
