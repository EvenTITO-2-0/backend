from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.work_slot import WorkSlotModel
from app.repository.crud_repository import Repository


class WorkSlotRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkSlotModel)
