import logging
from datetime import datetime
from uuid import UUID

from app.database.models.event_room_slot import EventRoomSlotModel
from app.services.services import BaseService
from app.repository.events_repository import EventsRepository
from app.repository.slots_repository import SlotsRepository
from app.schemas.events.slot import SlotSchema

from app.database.models.work import WorkStates
from app.repository.works_repository import WorksRepository
from app.repository.work_slot_repository import WorkSlotRepository

from app.database.models import WorkSlotModel

logger = logging.getLogger(__name__)

class SlotsConfigurationService(BaseService):
    def __init__(self, event_id: UUID, events_repository: EventsRepository,
                 slots_repository: SlotsRepository,
                 works_repository: WorksRepository,
                 work_slot_repository: WorkSlotRepository):
        self.event_id = event_id
        self.events_repository = events_repository
        self.slots_repository = slots_repository
        self.works_repository = works_repository
        self.work_slot_repository = work_slot_repository

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

    async def assign_works_to_slots(self):
        MAX_WORKS_PER_SLOT = 3
        logger.info(f"Starting assignment of works to slots for event {self.event_id}")
        logger.warning(f"Using hardcoded MAX_WORKS_PER_SLOT = {MAX_WORKS_PER_SLOT}")

        # 1. Fetch all slots, with their existing work links and works
        # We assume get_by_event_id_with_works correctly eager loads
        # slot.work_links and link.work.
        all_slots = await self.slots_repository.get_by_event_id_with_works(self.event_id)

        # 2. Fetch all works for the event
        # Using a high limit to get all works, assuming no pagination needed here.
        all_works = await self.works_repository.get_all_works_for_event(self.event_id, offset=0, limit=9999)

        # 3. Filter for assignable works (APPROVED) and available slots ('slot' type)
        assignable_works = [w for w in all_works if w.state == WorkStates.APPROVED]
        available_slots = [s for s in all_slots if s.slot_type == 'slot']
        available_slots.sort(key=lambda s: s.start)  # Sort slots chronologically

        logger.info(f"Found {len(assignable_works)} approved works and {len(available_slots)} available 'slot' type slots.")

        # 4. Build helper data structures for existing assignments
        assigned_work_ids = set()
        slot_assignments = {}  # {slot_id: {"track": str, "work_count": int}}
        track_schedule = {}  # {track_name: list[(start_time, end_time)]}

        for slot in available_slots:
            if slot.work_links:  # Assumes 'work_links' is loaded
                # We assume the repo eager loaded the nested .work relationship
                first_work = slot.work_links[0].work
                track = first_work.track
                work_count = len(slot.work_links)

                slot_assignments[slot.id] = {"track": track, "work_count": work_count}

                # Add to track schedule to check for overlaps
                if track not in track_schedule:
                    track_schedule[track] = []
                track_schedule[track].append((slot.start, slot.end))

                for link in slot.work_links:
                    assigned_work_ids.add(link.work.id)

        logger.info(f"{len(assigned_work_ids)} works are already assigned.")

        # 5. Group unassigned works by track
        unassigned_works_by_track = {}
        for work in assignable_works:
            if work.id not in assigned_work_ids:
                unassigned_works_by_track.setdefault(work.track, []).append(work)

        # Sort tracks to process those with more works first (a simple heuristic)
        sorted_tracks_to_assign = sorted(
            unassigned_works_by_track.items(),
            key=lambda item: len(item[1]),
            reverse=True
        )

        # 6. Assignment Logic
        new_links_to_create: list[WorkSlotModel] = []

        for track, works_to_assign in sorted_tracks_to_assign:
            work_iterator = iter(works_to_assign)
            current_work = next(work_iterator, None)

            if not current_work:
                continue  # No works to assign for this track

            logger.info(f"Attempting to assign {len(works_to_assign)} works for track '{track}'")

            for slot in available_slots:
                if not current_work:
                    break  # All works for this track are assigned

                total_capacity = MAX_WORKS_PER_SLOT  # Using hardcoded value
                current_fill = 0
                slot_track = None

                if slot.id in slot_assignments:
                    assignment = slot_assignments[slot.id]
                    current_fill = assignment["work_count"]
                    slot_track = assignment["track"]

                # --- Check Constraints ---

                # Constraint 1: Slot Purity. Can this slot accept this track?
                if slot_track and slot_track != track:
                    logger.debug(f"Exited in Constraint slot purity")
                    continue  # Slot is already assigned to a different track

                # Constraint: Capacity. Is this slot full?
                if current_fill >= total_capacity:
                    logger.debug(f"Exited in Constraint capacity")
                    continue  # Slot is full

                # Constraint 2: Track Overlap.
                # Does this slot overlap with another slot *already* assigned to this *same* track?
                is_overlapping = False
                for existing_start, existing_end in track_schedule.get(track, []):
                    # Check if it's the *same* slot (which is fine)
                    is_same_slot = (slot.start == existing_start and slot.end == existing_end)

                    # Check for overlap: (StartA < EndB) and (EndA > StartB)
                    if (slot.start < existing_end and slot.end > existing_start) and not is_same_slot:
                        is_overlapping = True
                        logger.debug(f"Exited in Constraint track overlap")
                        break  # This slot overlaps with another for the same track

                if is_overlapping:
                    logger.debug(f"Slot {slot.id} ({slot.start} - {slot.end}) overlaps with existing slot for track '{track}'")
                    continue  # Can't use this slot

                # --- If all checks pass, assign works ---
                remaining_capacity = total_capacity - current_fill

                while remaining_capacity > 0 and current_work:
                    logger.debug(f"Assigning work {current_work.id} (Track: {track}) to slot {slot.id} (Room: {slot.room_name})")

                    new_links_to_create.append(
                        WorkSlotModel(slot_id=slot.id, work_id=current_work.id)
                    )

                    remaining_capacity -= 1
                    current_fill += 1

                    # Update our tracking data *immediately*
                    if slot.id not in slot_assignments:
                        logger.debug(f"Initializing slot assignment tracking for slot {slot.id}")
                        # This is the first time we're using this slot
                        slot_assignments[slot.id] = {"track": track, "work_count": 0}
                        # Add to schedule only when we first assign to it
                        track_schedule.setdefault(track, []).append((slot.start, slot.end))

                    slot_assignments[slot.id]["work_count"] = current_fill

                    # Get next work
                    current_work = next(work_iterator, None)

            if current_work:
                logger.warning(f"Not all works for track '{track}' could be assigned. Remaining work ID: {current_work.id}")
                # If we finished iterating all slots and still have work, log a warning
                logger.warning(f"Could not find slots for all works in track '{track}'. Work {current_work.id} and possibly others remain unassigned.")

        # 7. Persist new assignments to the database
        if new_links_to_create:
            logger.info(f"Committing {len(new_links_to_create)} new work-slot assignments.")
            # We use the session from one of our repositories
            self.work_slot_repository.session.add_all(new_links_to_create)
            await self.work_slot_repository.session.flush()
            await self.work_slot_repository.session.commit()
        else:
            logger.info("No new work-slot assignments were needed.")

        logger.info(f"Finished assigning works to slots for event {self.event_id}")