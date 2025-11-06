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

    async def remove_for_work_id(self, work_id: UUID) -> int:
        """
        Deletes all work-slot links associated with a given work_id.
        Returns the number of links deleted.
        """
        logger.info(f"Deleting all work-slot links for work {work_id}")

        stmt = (
            WorkSlotModel.__table__.delete()
            .where(WorkSlotModel.work_id == work_id)
            .returning(WorkSlotModel.work_id)
        )

        result = await self.session.execute(stmt)
        deleted_count = len(result.all())
        await self.session.flush()

        logger.info(f"Deleted {deleted_count} work-slot links for work {work_id}.")
        await self.session.commit()
        return deleted_count

    async def add_work_to_slot_by_id(self, slot_id: int, work_id: UUID) -> WorkSlotModel:
        """
        Creates a link between a work and a slot.
        If the link already exists, it won't create a duplicate.
        Returns the created WorkSlotModel instance.
        """
        logger.info(f"Linking work {work_id} to slot {slot_id}")

        # Check if the link already exists to avoid duplicates
        stmt = select(WorkSlotModel).where(
            WorkSlotModel.slot_id == slot_id,
            WorkSlotModel.work_id == work_id,
        )
        existing_link = await self.session.scalar(stmt)

        if existing_link:
            logger.warning(f"Work {work_id} is already linked to slot {slot_id}")
            return existing_link

        # Create the new work-slot link
        work_slot_link = WorkSlotModel(slot_id=slot_id, work_id=work_id)
        self.session.add(work_slot_link)

        await self.session.flush()
        await self.session.commit()

        logger.info(f"Successfully linked work {work_id} to slot {slot_id}")
        return work_slot_link