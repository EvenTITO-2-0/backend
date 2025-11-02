import logging
from datetime import datetime
from uuid import UUID

from app.database.models.event_room_slot import EventRoomSlotModel
from app.schemas.events.assing_works_parameters import AssignWorksParametersSchema
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
            return

        entries = []
        for slot in slots:
            logger.info(f"Processing slot: {slot}")
            slot_type = slot.get('type')
            start = slot.get('start')
            end = slot.get('end')
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

    async def get_slots_with_works(self):
        logger.info(f"Fetching slots with works for event {self.event_id}")
        slots = await self.slots_repository.get_by_event_id_with_works(self.event_id)
        logger.info(f"Fetched {len(slots)} slots with works for event {self.event_id}")
        logger.info(f"Slots obtained: {slots}")
        return slots

    async def assign_works_to_slots2(self, parameters: AssignWorksParametersSchema):
        logger.info(f"Starting assignment with parameters: {parameters}")

        if parameters.reset_previous_assignments:
            logger.info("Resetting previous assignments...")
            await self.work_slot_repository.delete_by_event_id(self.event_id)
            # Note: We don't need to re-fetch all_slots, as the slot.work_links
            # will just be empty, which the algorithm handles.

        # 1. Fetch all slots, with their existing work links and works
        all_slots = await self.slots_repository.get_by_event_id_with_works(self.event_id)

        # 2. Fetch all works for the event
        all_works = await self.works_repository.get_all_works_for_event(self.event_id, offset=0, limit=9999)

        # 3. Filter for assignable works (APPROVED) and available slots ('slot' type)
        assignable_works = [w for w in all_works if w.state == WorkStates.APPROVED] # TODO obtenerlos asi de la bdd
        available_slots = [s for s in all_slots if s.slot_type == 'slot'] # TODO obtenerlos asi de la bdd
        available_slots.sort(key=lambda s: s.start)

        logger.info(
            f"Found {len(assignable_works)} approved works and {len(available_slots)} available 'slot' type slots.")

        # 4. Build helper data structures (this is correct, handles both reset=True/False)
        assigned_work_ids = set()
        slot_assignments = {}  # {slot_id: {"track": str, "work_count": int}}
        track_schedule = {}  # {track_name: list[(start_time, end_time)]}

        for slot in available_slots:
            if slot.work_links:
                # This logic is fine. If we reset, slot.work_links will be empty
                # and this block will be skipped.
                first_work = slot.work_links[0].work
                track = first_work.track
                work_count = len(slot.work_links)
                slot_assignments[slot.id] = {"track": track, "work_count": work_count}
                if track not in track_schedule:
                    track_schedule[track] = []
                track_schedule[track].append({"id": slot.id, "start": slot.start, "end": slot.end})
                for link in slot.work_links:
                    assigned_work_ids.add(link.work.id)

        logger.info(f"{len(assigned_work_ids)} works are already assigned.")

        # 5. Group unassigned works by track (this is correct)
        unassigned_works_by_track = {}
        for work in assignable_works:
            if work.id not in assigned_work_ids:
                unassigned_works_by_track.setdefault(work.track, []).append(work)

        sorted_tracks_to_assign = sorted(
            unassigned_works_by_track.items(),
            key=lambda item: len(item[1]),
            reverse=True
        )

        # 6. Assignment Logic
        new_links_to_create: list[WorkSlotModel] = []

        time_per_work_minutes = parameters.time_per_work
        if time_per_work_minutes <= 0:
            logger.error("Time per work must be positive. Aborting assignment.")
            return  # Or raise an exception

        for track, works_to_assign in sorted_tracks_to_assign:
            work_iterator = iter(works_to_assign)
            current_work = next(work_iterator, None)
            if not current_work:
                continue
            logger.info(f"Attempting to assign {len(works_to_assign)} works for track '{track}'")

            for slot in available_slots:
                if not current_work:
                    break

                slot_duration_seconds = (slot.end - slot.start).total_seconds()
                slot_duration_minutes = slot_duration_seconds / 60

                # Calculate capacity based on slot duration and time_per_work
                total_capacity = int(slot_duration_minutes // time_per_work_minutes)

                if total_capacity == 0:
                    logger.warning(
                        f"Slot {slot.id} is too short ({slot_duration_minutes} min) for works ({time_per_work_minutes} min). Skipping.")
                    continue

                current_fill = 0
                slot_track = None

                if slot.id in slot_assignments:
                    assignment = slot_assignments[slot.id]
                    current_fill = assignment["work_count"]
                    slot_track = assignment["track"]

                if slot_track and slot_track != track:
                    continue
                if current_fill >= total_capacity:
                    continue

                # (Track Overlap constraint is correct)
                is_overlapping = False
                for existing_id, existing_start, existing_end in track_schedule.get(track, []):
                    is_same_slot = slot.id == existing_id
                    #is_same_slot = (slot.start == existing_start and slot.end == existing_end)
                    if (slot.start < existing_end and slot.end > existing_start) and not is_same_slot:
                        is_overlapping = True
                        break
                if is_overlapping:
                    continue

                remaining_capacity = total_capacity - current_fill

                while remaining_capacity > 0 and current_work:
                    logger.debug(
                        f"Assigning work {current_work.id} (Track: {track}) to slot {slot.id} (Capacity: {current_fill}/{total_capacity})")
                    new_links_to_create.append(
                        WorkSlotModel(slot_id=slot.id, work_id=current_work.id)
                    )
                    remaining_capacity -= 1
                    current_fill += 1
                    if slot.id not in slot_assignments:
                        slot_assignments[slot.id] = {"track": track, "work_count": 0}
                        track_schedule.setdefault(track, []).append((slot.start, slot.end))
                    slot_assignments[slot.id]["work_count"] = current_fill
                    current_work = next(work_iterator, None)

            if current_work:
                logger.warning(
                    f"Could not find slots for all works in track '{track}'. Work {current_work.id} and possibly others remain unassigned.")

        # 7. Persist new assignments to the database
        if new_links_to_create:
            logger.info(f"Committing {len(new_links_to_create)} new work-slot assignments.")
            self.work_slot_repository.session.add_all(new_links_to_create)
            await self.work_slot_repository.session.flush()
            await self.work_slot_repository.session.commit()
        else:
            logger.info("No new work-slot assignments were needed.")

        logger.info(f"Finished assigning works to slots for event {self.event_id}")


    async def assign_works_to_slots(self, parameters: AssignWorksParametersSchema):
        logger.info(f"Starting assignment with parameters: {parameters}")

        if parameters.reset_previous_assignments:
            logger.info("Resetting previous assignments...")
            await self.work_slot_repository.delete_by_event_id(self.event_id)

        #all_slots = await self.slots_repository.get_by_event_id_with_works(self.event_id)
        #available_slots = [s for s in all_slots if s.slot_type == 'slot'] # TODO obtenerlos asi de la bdd
        available_slots = await self.slots_repository.get_slots_by_event_id_with_works(self.event_id)

        #all_works = await self.works_repository.get_all_works_for_event(self.event_id, offset=0, limit=9999)
        #assignable_works = [w for w in all_works if w.state == WorkStates.APPROVED] # TODO obtenerlos asi de la bdd
        assignable_works = await self.works_repository.get_all_approved_works_for_event(self.event_id, offset=0, limit=9999)
        logger.info(f"Found {len(assignable_works)} approved works and {len(available_slots)} available 'slot' type slots.")

        new_links_to_create: list[WorkSlotModel] = []
        available_slots_by_room = {}
        available_spaces_by_room = {}
        for slot in available_slots:
            slot_duration_minutes = (slot.end - slot.start).total_seconds() / 60
            total_capacity = int(slot_duration_minutes // parameters.time_per_work)
            slot.available_space =  total_capacity - len(slot.work_links)
            available_slots_by_room.setdefault(slot.room_name, []).append(slot)

        for room_name in available_slots_by_room: # Ordenar por inicio
            available_slots_by_room[room_name].sort(key=lambda s: s.start)

        for room_name, slots in available_slots_by_room.items():
            available_spaces_by_room[room_name] = sum(s.available_space for s in slots)

        assignable_works_by_track = {}
        for work in assignable_works:
            assignable_works_by_track.setdefault(work.track, []).append(work)

        sorted_track_names = sorted(
            assignable_works_by_track.keys(),
            key=lambda some_track_name: len(assignable_works_by_track[some_track_name]),
            reverse=True
        )
        # crear room preferenciales buscando works ya asignados
        last_works_assigned = -1
        while last_works_assigned != len(new_links_to_create):
            last_works_assigned = len(new_links_to_create)
            sorted_rooms_names = sorted(
                available_spaces_by_room.keys(),
                key=available_spaces_by_room.get,
                reverse=False
            )
            for track_name in sorted_track_names:
                works = assignable_works_by_track[track_name]
                room_with_most_space = sorted_rooms_names.pop()
                # if available_slots_by_room[room_with_most_space] < len(works):
                # handleGetRoomCombinationsThatMaximizeSpace()
                slots_for_room = available_slots_by_room[room_with_most_space]

                unassigned_works_for_this_track = []
                for work in works:
                    assigned = False
                    for slot in slots_for_room:
                        if slot.available_space > 0:
                            logger.debug(
                                f"Assigning work {work.id} (Track: {track_name}) to slot {slot.id} in room {room_with_most_space} (Available Space: {slot.available_space})")
                            new_links_to_create.append(
                                WorkSlotModel(slot_id=slot.id, work_id=work.id)
                            )
                            slot.available_space -= 1
                            available_spaces_by_room[room_with_most_space] -= 1
                            assigned = True
                            break
                    if not assigned:
                        logger.warning(f"Could not find a slot with available space for work {work.id} in track '{track_name}'.")
                        unassigned_works_for_this_track.append(work)

                assignable_works_by_track[track_name] = unassigned_works_for_this_track


        # 7. Persist new assignments to the database
        if new_links_to_create:
            logger.info(f"Committing {len(new_links_to_create)} new work-slot assignments.")
            self.work_slot_repository.session.add_all(new_links_to_create)
            await self.work_slot_repository.session.flush()
            await self.work_slot_repository.session.commit()
        else:
            logger.info("No new work-slot assignments were needed.")

        logger.info(f"Finished assigning works to slots for event {self.event_id}")