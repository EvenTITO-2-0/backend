from uuid import UUID

from sqlalchemy import desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.submission import SubmissionModel
from app.repository.crud_repository import Repository
from app.schemas.works.submission import SubmissionSchema
from app.utils.utils import now_datetime


class SubmissionsRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SubmissionModel)

    async def get_all_submissions_for_event(
        self, event_id: UUID, work_id: UUID, offset: int, limit: int
    ) -> list[SubmissionModel]:
        conditions = [self.model.event_id == event_id, self.model.work_id == work_id]
        return await self._get_many_with_conditions(conditions, offset, limit)

    async def get_last_submission(self, event_id, work_id) -> SubmissionSchema:
        return await self._get_with_conditions(
            [
                self.model.event_id == event_id,
                self.model.work_id == work_id,
            ],
            order_by=desc(self.model.creation_date),
        )

    async def do_new_submit(self, event_id: UUID, work_id: UUID) -> UUID:
        new_submission = SubmissionModel(event_id=event_id, work_id=work_id)
        return (await self._create(new_submission)).id

    async def update_submit(self, submission_id: UUID) -> UUID:
        now = now_datetime()
        update_query = update(self.model).where(self.model.id == submission_id).values(last_update=now)
        await self.session.execute(update_query)
        await self.session.commit()
        return submission_id
