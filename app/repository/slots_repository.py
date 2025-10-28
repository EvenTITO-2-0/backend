import logging
from typing import Sequence

from sqlalchemy import select  # <-- ADD THIS
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # <-- ADD THIS

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
        Deletes all EventRoomSlotModel entries associated with the given event_id.

        Args:
            event_id: The ID of the event whose slots are to be deleted.
        """
        logger.info(f"Deleting event room slots for event {event_id}")
        await self.session.execute(
            EventRoomSlotModel.__table__.delete().where(EventRoomSlotModel.event_id == event_id)
        )
        await self.session.flush()
        logger.info(f"Successfully deleted event room slots for event {event_id}")

    async def get_by_event_id_with_works(self, event_id: str) -> Sequence[EventRoomSlotModel]:
        """
        Fetches all slots for a given event, eagerly loading
        the associated 'works' relationship for each slot.

        Args:
            event_id: The ID of the event to fetch slots for.

        Returns:
            A sequence of EventRoomSlotModel instances, with the
            'works' attribute already populated.
        """
        logger.info(f"Fetching slots and associated works for event {event_id}")

        stmt = (
            select(EventRoomSlotModel)
            .where(EventRoomSlotModel.event_id == event_id)
            .options(selectinload(EventRoomSlotModel.work_links))
        )

        # 3. Execute and return the results
        result = await self.session.scalars(stmt)
        return result.unique().all()