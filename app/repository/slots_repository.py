import logging
from typing import Sequence

from sqlalchemy import select  # <-- ADD THIS
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # <-- ADD THIS

from app.database.models import WorkSlotModel
from app.database.models.event_room_slot import EventRoomSlotModel
from app.repository.crud_repository import Repository

logger = logging.getLogger(__name__)


class SlotsRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, EventRoomSlotModel)

    async def bulk_create(self, entries: Sequence[EventRoomSlotModel]) -> None:
        """
        Adds multiple EventRoomSlotModel instances to the session for bulk insertion.

        The actual commit should be handled by the unit of work/service layer
        to ensure transactional integrity. This method just adds the objects
        to the session and flushes.

        Args:
            entries: A sequence of EventRoomSlotModel objects to be created.
        """
        logger.info(f"Bulk creating {len(entries)} event room slots")
        self.session.add_all(entries)
        await self.session.flush()
        logger.info(f"Successfully added {len(entries)} event room slots to the session")

    async def delete_by_event_id(self, event_id) -> None:
        """
        Deletes all EventRoomSlotModel entries associated with the given event_id,
        and also deletes their associated WorkSlotModel links.
        """
        logger.info(f"Deleting work assignments for event {event_id}")

        subquery = select(EventRoomSlotModel.id).where(EventRoomSlotModel.event_id == event_id).scalar_subquery()
        await self.session.execute(WorkSlotModel.__table__.delete().where(WorkSlotModel.slot_id.in_(subquery)))

        logger.info(f"Deleting event room slots for event {event_id}")
        await self.session.execute(EventRoomSlotModel.__table__.delete().where(EventRoomSlotModel.event_id == event_id))

        await self.session.flush()
        logger.info(f"Successfully deleted all slots and associations for event {event_id}")

    # --- END REPLACE ---
    async def get_by_event_id_with_works(self, event_id: str) -> Sequence[EventRoomSlotModel]:
        """
        Fetches all slots for a given event, eagerly loading
        the associated 'work_links' AND the nested 'work' for each link.
        """
        logger.info(f"Fetching slots and associated works for event {event_id}")

        stmt = (
            select(EventRoomSlotModel)
            .where(EventRoomSlotModel.event_id == event_id)
            .options(selectinload(EventRoomSlotModel.work_links).selectinload(WorkSlotModel.work))
        )

        result = await self.session.scalars(stmt)
        return result.unique().all()

    async def get_slots_by_event_id_with_works(self, event_id: str) -> Sequence[EventRoomSlotModel]:
        logger.info(f"Fetching slots and associated work links for event {event_id}")
        conditions = [EventRoomSlotModel.event_id == event_id, EventRoomSlotModel.slot_type == "slot"]
        load_options = selectinload(EventRoomSlotModel.work_links).selectinload(WorkSlotModel.work)
        return await self._get_many_with_conditions(conditions, offset=0, limit=1000, options=[load_options])
