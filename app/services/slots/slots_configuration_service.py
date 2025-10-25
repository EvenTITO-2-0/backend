import logging
from datetime import datetime
from uuid import UUID

from app.database.models.event_room_slot import EventRoomSlotModel
from app.services.services import BaseService
from app.repository.events_repository import EventsRepository
from app.repository.slots_repository import SlotsRepository
from app.schemas.events.slot import SlotSchema

logger = logging.getLogger(__name__)

class SlotsConfigurationService(BaseService):
    def __init__(self, event_id: UUID, events_repository: EventsRepository, slots_repository: SlotsRepository):
        self.event_id = event_id
        self.events_repository = events_repository
        self.slots_repository = slots_repository

    async def configure_event_slots_and_rooms(self):
        logger.info(f"Configuring slots and rooms for event {self.event_id}")
        event = await self.events_repository.get(self.event_id)
        slots = event.mdata.get('slots', [])
        rooms = event.mdata.get('rooms', [])
        was_configured = event.mdata.get('was_configured', False)
        if was_configured:
            return  # Already configured

        entries = []
        for slot in slots:
            logger.info(f"Processing slot: {slot}")
            slot_type = slot.get('type')
            start = slot.get('start')
            end = slot.get('end')
            # Convert to datetime if needed
            if isinstance(start, str):
                start = datetime.fromisoformat(start)
            if isinstance(end, str):
                end = datetime.fromisoformat(end)
            if slot_type in ('slot', 'break'):
                logger.info(f"Creating slots for type '{slot_type}' in all rooms")
                for room in rooms:
                    entries.append(EventRoomSlotModel(
                        event_id=self.event_id,
                        room_name=room.get('name'),
                        slot_type=slot_type,
                        start=start,
                        end=end
                    ))
            elif slot_type == 'plenary':
                logger.info(f"Creating slot for plenary session in room '{rooms[0].get('name')}'")
                entries.append(EventRoomSlotModel(
                    event_id=self.event_id,
                    # TODO setear una sala particular para una pleanaria
                    room_name=rooms[0].get('name'),
                    slot_type=slot_type,
                    start=start,
                    end=end
                ))
        await self.slots_repository.bulk_create(entries)
        event.mdata['was_configured'] = True
        await self.events_repository.update(self.event_id, {"mdata": event.mdata})
        logger.info(f"Finished configuring slots and rooms for event {self.event_id}")

    async def delete_event_slots_and_rooms(self):
        logger.info(f"Deleting slots and rooms for event {self.event_id}")
        await self.slots_repository.delete_by_event_id(self.event_id)
        event = await self.events_repository.get(self.event_id)
        event.mdata['was_configured'] = False
        await self.events_repository.update(self.event_id, {"mdata": event.mdata})
        logger.info(f"Finished deleting slots and rooms for event {self.event_id}")

    async def delete_event_slot(self, slot_id: int) -> None:
        """Delete a single event room slot by its id."""
        logger.info(f"Deleting slot {slot_id} for event {self.event_id}")
        # repository.remove will fetch and delete the object and commit
        await self.slots_repository.remove(slot_id)
        logger.info(f"Deleted slot {slot_id} for event {self.event_id}")

    async def create_event_slot(self, new_slot: SlotSchema) -> EventRoomSlotModel:
        logger.info(f"Creating single slot for event {self.event_id}: {new_slot}")
        db_in = EventRoomSlotModel(
            event_id=self.event_id,
            room_name=new_slot.room_name,
            slot_type=new_slot.type,
            start=new_slot.start,
            end=new_slot.end,
        )
        created = await self.slots_repository._create(db_in)
        logger.info(f"Created slot {created.id} for event {self.event_id}")
        return created

    async def update_event_slot(self, slot_id: int, new_slot: SlotSchema) -> bool:
        logger.info(f"Updating slot {slot_id} for event {self.event_id} with {new_slot}")
        update_data = {
            "room_name": new_slot.room_name,
            "slot_type": new_slot.type,
            "start": new_slot.start,
            "end": new_slot.end,
        }
        result = await self.slots_repository.update(slot_id, update_data)
        logger.info(f"Updated slot {slot_id} for event {self.event_id}")
        return result
