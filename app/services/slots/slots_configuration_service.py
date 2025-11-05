import copy
import logging
from datetime import datetime, timedelta
from uuid import UUID

from app.database.models.event_room_slot import EventRoomSlotModel
from app.schemas.events.assing_works_parameters import AssignWorksParametersSchema
from app.services.services import BaseService
from app.repository.events_repository import EventsRepository
from app.repository.slots_repository import SlotsRepository
from app.schemas.events.slot import SlotSchema

from app.database.models.work import WorkStates, WorkModel
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

    async def delete_slot_work(self, work_id: UUID):
        logger.info(f"Removing assignment for work {work_id}")
        await self.work_slot_repository.remove_for_work_id(work_id)
        logger.info(f"Removed assignment for work {work_id}")

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
        """
        (This is your main function from the class 'YourAssignmentService')
        """
        logger.info(f"Starting new optimal assignment with parameters: {parameters}")

        # --- 1. Data Fetching ---
        if parameters.reset_previous_assignments:
            logger.info("Resetting previous assignments...")
            await self.work_slot_repository.delete_by_event_id(self.event_id)

        available_slots = await self.slots_repository.get_slots_by_event_id_with_works(self.event_id)
        assignable_works = await self.works_repository.get_all_approved_works_for_event(self.event_id, offset=0,
                                                                                        limit=9999)

        if not assignable_works or not available_slots:
            logger.warning("No assignable works or available slots.")
            return {"message": "No works or slots to assign."}

        # --- 2. Define Penalties ---
        # You can customize these priorities
        penalties = CostPenalties(
            unassigned_work=20,  # Highest cost
            per_distinct_day=10,
            per_room_track_mix=5
        )

        # --- 3. (Optional but Recommended) Run Greedy Algorithm ---
        # Running a fast greedy algorithm first gives a *much* better
        # initial bound, which makes the B&B search prune faster.
        # For this example, we'll just use infinity.
        initial_greedy_cost = float('inf')

        # --- 4. Run Branch and Bound Algorithm ---
        logger.info("Starting Branch and Bound search for optimal cost...")

        # Pass deepcopies so the original data isn't modified
        scheduler = ConfigurableBBScheduler(
            works=copy.deepcopy(assignable_works),
            slots=copy.deepcopy(available_slots),
            time_per_work=parameters.time_per_work,
            penalties=penalties
        )

        # Pass the greedy solution's cost as the initial bound
        optimal_assignments_list, optimal_cost = scheduler.solve(
            greedy_cost_bound=initial_greedy_cost
        )

        # --- 5. Finalization ---
        assignments_created = len(optimal_assignments_list)
        unassigned_works = len(assignable_works) - assignments_created

        logger.info(f"Optimal assignment complete. Final Cost: {optimal_cost}")
        logger.info(f"Assignments: {assignments_created}, Unassigned: {unassigned_works}")

        new_links_to_create = [
            WorkSlotModel(work_id=work.id, slot_id=slot.id)
            for work, slot in optimal_assignments_list
        ]

        if new_links_to_create:
            # Assuming a bulk_create method on your repository
            self.work_slot_repository.session.add_all(new_links_to_create)
            await self.work_slot_repository.session.flush()
            await self.work_slot_repository.session.commit()
            logger.info("Successfully saved optimal assignments to the database.")

        return {
            "assignments_created": assignments_created,
            "unassigned_works": unassigned_works,
            "final_cost": optimal_cost,
            "is_optimal": True
        }


import copy
from datetime import timedelta, date
from dataclasses import dataclass, field
from typing import Set, Dict, List, Tuple


@dataclass
class CostPenalties:
    unassigned_work: int = 10000
    per_distinct_day: int = 100
    per_room_track_mix: int = 10


@dataclass
class SearchState:
    """
    MODIFIED: Holds the state for a slot-centric decision tree.
    """
    # We are now making a decision for the slot at this index
    slot_index: int = 0
    current_cost: float = 0.0

    # Solution being built (maps slot.id -> track_name)
    slot_track_map: Dict[int, str] = field(default_factory=dict)

    # Constraint tracking
    # How many works for each track still need to be assigned
    track_work_counts_remaining: Dict[str, int] = field(default_factory=dict)
    # What time intervals are blocked for each track (to prevent parallel scheduling)
    track_time_usage: Dict[str, List[Tuple[date, date]]] = field(default_factory=dict)

    # Cost tracking
    days_used: Set[date] = field(default_factory=set)
    room_track_map: Dict[str, Set[str]] = field(default_factory=dict)


class ConfigurableBBScheduler:
    """
    MODIFIED: A Branch and Bound scheduler that decides which track
    to assign to each slot.
    """

    def __init__(self, works: List[WorkModel], slots: List[EventRoomSlotModel],
                 time_per_work: int, penalties: CostPenalties):

        self.penalties = penalties
        self.time_delta = timedelta(minutes=time_per_work)

        # --- Store Track and Work info ---
        self.works_by_track: Dict[str, List[WorkModel]] = {}
        for w in works:
            self.works_by_track.setdefault(w.track, []).append(w)

        self.track_counts: Dict[str, int] = {
            track: len(works_list)
            for track, works_list in self.works_by_track.items()
        }
        self.total_works = len(works)
        self.available_tracks = list(self.track_counts.keys())

        # --- Store Slot info ---
        # Calculate true available space for each slot
        for slot in slots:
            slot_duration = (slot.end - slot.start).total_seconds() / 60
            # Note: available_space is the *original* capacity
            slot.available_space = int(slot_duration // time_per_work) - len(slot.work_links)

        # Sort all slots. Heuristic: Sort by start time, then room.
        # This groups slots together logically.
        self.all_slots: List[EventRoomSlotModel] = sorted(slots, key=lambda s: (s.start, s.room_name))
        self.slot_map: Dict[int, EventRoomSlotModel] = {s.id: s for s in self.all_slots}
        self.total_slots = len(self.all_slots)

        # --- B&B Root Node ---
        self.global_best_cost = float('inf')
        self.global_best_solution: Dict[int, str] = {}  # Will be {slot_id: track_name}

        self.initial_state = SearchState(
            # Start with the full count of works needed for each track
            track_work_counts_remaining=copy.deepcopy(self.track_counts)
        )

    def solve(self, greedy_cost_bound=float('inf')):
        """
        Starts the B&B search.
        """
        logger.info(f"Starting B&B with initial cost bound: {greedy_cost_bound}")
        self.global_best_cost = greedy_cost_bound

        self._search(self.initial_state)

        logger.info(f"B&B search complete. Optimal cost found: {self.global_best_cost}")

        # --- MODIFIED: Post-processing ---
        # Convert the solution of {slot_id: track_name}
        # back to List[(WorkModel, SlotModel)]
        final_work_assignments = []
        works_map_copy = {track: list(works) for track, works in self.works_by_track.items()}

        for slot_id, track_name in self.global_best_solution.items():
            slot = self.slot_map[slot_id]
            # Get the *original* capacity of this slot
            works_to_place_in_slot = slot.available_space

            for _ in range(works_to_place_in_slot):
                # Check if we still have works for this track
                if works_map_copy[track_name]:
                    work_obj = works_map_copy[track_name].pop()
                    final_work_assignments.append((work_obj, slot))
                else:
                    # Slot had more space than the track had works,
                    # so we stop filling it.
                    break

        return final_work_assignments, self.global_best_cost

    def _calculate_bound(self, state: SearchState) -> float:
        """
        PRUNING FUNCTION (Optimistic Cost)
        Calculates the "best case" cost from this state.
        """
        current_cost = state.current_cost

        # Calculate minimum cost for works not yet assigned
        works_still_needed = sum(state.track_work_counts_remaining.values())

        # Calculate best-case future capacity
        total_remaining_space = 0
        for i in range(state.slot_index, self.total_slots):
            total_remaining_space += self.all_slots[i].available_space

        future_unassigned_works = max(0, works_still_needed - total_remaining_space)

        # Bound = current cost + best possible future cost
        return current_cost + (future_unassigned_works * self.penalties.unassigned_work)

    def _search(self, state: SearchState):
        """
        The recursive core of the Branch and Bound algorithm.
        Decides which track to assign to the slot at `state.slot_index`.
        """

        # --- 1. Base Case (Leaf Node) ---
        # If we have made a decision for every slot...
        if state.slot_index >= self.total_slots:
            # We must add the cost of all works that *still* haven't been assigned
            unassigned_works = sum(state.track_work_counts_remaining.values())
            final_cost = state.current_cost + (unassigned_works * self.penalties.unassigned_work)

            if final_cost < self.global_best_cost:
                logger.info(f"New best solution found! Cost: {final_cost}")
                self.global_best_cost = final_cost
                self.global_best_solution = dict(state.slot_track_map)  # Store copy
            return

        # --- 2. Pruning ---
        optimistic_cost_bound = self._calculate_bound(state)
        if optimistic_cost_bound >= self.global_best_cost:
            # logger.info(f"Pruning branch...")
            return

        # --- 3. Branching ---
        slot_to_try = self.all_slots[state.slot_index]

        # --- Branch 1: Try to *assign a track* to this slot ---
        # We can only assign tracks that still need works
        tracks_with_remaining_works = [
            t for t in self.available_tracks
            if state.track_work_counts_remaining.get(t, 0) > 0
        ]

        for track_name in tracks_with_remaining_works:

            # --- Constraint Check: Parallel Time Conflict ---
            # Check if this track is already scheduled at this time
            is_conflict = False
            for existing_start, existing_end in state.track_time_usage.get(track_name, []):
                # Check for overlap: (StartA < EndB) and (EndA > StartB)
                if slot_to_try.start < existing_end and slot_to_try.end > existing_start:
                    is_conflict = True
                    break

            if is_conflict:
                continue  # This track cannot be assigned to this slot

            # --- If valid, calculate cost and recurse ---

            # How many works will this slot "consume" from the track?
            works_this_slot_can_take = slot_to_try.available_space
            works_this_track_needs = state.track_work_counts_remaining[track_name]
            works_to_assign = min(works_this_slot_can_take, works_this_track_needs)

            # --- Calculate Incremental Cost ---
            cost_increase = 0
            day = slot_to_try.start.date()

            is_new_day = day not in state.days_used
            if is_new_day:
                cost_increase += self.penalties.per_distinct_day

            tracks_in_room = state.room_track_map.get(slot_to_try.room_name, set())
            is_new_track_in_room = track_name not in tracks_in_room
            is_room_mix = is_new_track_in_room and len(tracks_in_room) > 0
            if is_room_mix:
                cost_increase += self.penalties.per_room_track_mix

            # --- Modify State (Move Down the Tree) ---
            state.slot_index += 1
            state.current_cost += cost_increase
            state.slot_track_map[slot_to_try.id] = track_name
            state.track_work_counts_remaining[track_name] -= works_to_assign
            state.track_time_usage.setdefault(track_name, []).append((slot_to_try.start, slot_to_try.end))

            if is_new_day: state.days_used.add(day)
            if is_new_track_in_room: state.room_track_map.setdefault(slot_to_try.room_name, set()).add(track_name)

            # --- Recurse ---
            self._search(state)

            # --- Backtrack (Revert State / Move Up) ---
            if is_new_track_in_room: state.room_track_map[slot_to_try.room_name].remove(track_name)
            if is_new_day: state.days_used.remove(day)

            state.track_time_usage[track_name].pop()
            state.track_work_counts_remaining[track_name] += works_to_assign
            del state.slot_track_map[slot_to_try.id]
            state.current_cost -= cost_increase
            state.slot_index -= 1

        # --- Branch 2: *Skip* this slot (do not assign any track) ---

        # Modify State
        state.slot_index += 1

        # Recurse
        self._search(state)

        # Backtrack
        state.slot_index -= 1