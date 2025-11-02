import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import EventRoomSlotModel
from app.database.models.work_slot import WorkSlotModel
from app.repository.crud_repository import Repository

logger = logging.getLogger(__name__)

class WorkSlotRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkSlotModel)

    async def delete_by_event_id(self, event_id: UUID) -> int:
        """
        Deletes all work-slot links associated with a given event.
        Returns the number of links deleted.
        """
        logger.info(f"Deleting all work-slot links for event {event_id}")

        subquery = (
            select(EventRoomSlotModel.id)
            .where(EventRoomSlotModel.event_id == event_id)
            .scalar_subquery()
        )

        stmt = (
            WorkSlotModel.__table__.delete()
            .where(WorkSlotModel.slot_id.in_(subquery))
            .returning(WorkSlotModel.slot_id)
        )

        result = await self.session.execute(stmt)
        deleted_count = len(result.all())
        await self.session.flush()

        logger.info(f"Deleted {deleted_count} work-slot links.")
        return deleted_count