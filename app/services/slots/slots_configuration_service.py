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
        logger.info(f"Starting optimal assignment with parameters: {parameters}")

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
            unassigned_work=10000,  # Highest cost
            per_distinct_day=100,
            per_room_track_mix=10
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


import logging
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
    Holds the entire state of a single node in the B&B search tree.
    """
    work_index: int = 0
    current_cost: float = 0.0

    # Solution being built
    assignments: List[Tuple[WorkModel, EventRoomSlotModel]] = field(default_factory=list)

    # Constraint tracking
    track_time_usage: Dict[str, List[Tuple[date, date]]] = field(default_factory=dict)
    slot_cursors: Dict[int, date] = field(default_factory=dict)
    slot_available_space: Dict[int, int] = field(default_factory=dict)

    # Cost tracking
    days_used: Set[date] = field(default_factory=set)
    room_track_map: Dict[str, Set[str]] = field(default_factory=dict)  # e.g. en la sala 1 esta "Track A" y "Track B"

    slot_track_map: Dict[int, str] = field(default_factory=dict) # e.g. el slot 5 tiene asignado "Track A"


class ConfigurableBBScheduler:
    """
    A Branch and Bound scheduler that minimizes a configurable cost function
    with a hard constraint against mixing tracks in a single slot.
    """

    def __init__(self, works: List[WorkModel], slots: List[EventRoomSlotModel],
                 time_per_work: int, penalties: CostPenalties):

        self.penalties: CostPenalties
        self.time_delta: timedelta
        self.works_to_assign: List[WorkModel]
        self.all_slots: List[EventRoomSlotModel]

        self.penalties = penalties
        self.time_delta = timedelta(minutes=time_per_work)

        # Separo los trabajos por tracks
        works_by_track = {}
        for w in works:
            works_by_track.setdefault(w.track, []).append(w)

        # Se ordenan los tracks por cantidad de trabajos
        sorted_tracks = sorted(works_by_track.keys(), key=lambda t: len(works_by_track[t]), reverse=True)
        self.works_to_assign = [w for t in sorted_tracks for w in works_by_track[t]]

        # Ordenar salas por espacio disponible
        self.available_slots_by_room = {}
        room_total_space = {}
        for slot in slots:
            slot_duration = (slot.end - slot.start).total_seconds() / 60
            # Tener en cuenta links ya asignados (TODO revisar que funcione con links ya puestos)
            slot.available_space = int(slot_duration // time_per_work) - len(slot.work_links)
            self.available_slots_by_room.setdefault(slot.room_name, []).append(slot)
            room_total_space[slot.room_name] = room_total_space.get(slot.room_name, 0) + slot.available_space

        for room_name in self.available_slots_by_room:
            self.available_slots_by_room[room_name].sort(key=lambda s: s.start)

        self.sorted_room_names = sorted(room_total_space.keys(), key=lambda r: room_total_space[r], reverse=True)
        self.all_slots = slots

        # Nodo raiz
        self.total_works = len(self.works_to_assign)
        self.global_best_cost = float('inf')
        self.global_best_solution = []

        self.initial_state = SearchState(
            slot_cursors={s.id: s.start for s in self.all_slots},
            slot_available_space={s.id: s.available_space for s in self.all_slots}
        )

    def solve(self, greedy_cost_bound=float('inf')):
        """
        Starts the B&B search.
        A 'greedy_cost_bound' (from a greedy algorithm) is highly recommended.
        """
        logger.info(f"Starting B&B with initial cost bound: {greedy_cost_bound}")
        self.global_best_cost = greedy_cost_bound

        self._search(self.initial_state)

        logger.info(f"B&B search complete. Optimal cost found: {self.global_best_cost}")
        return self.global_best_solution, self.global_best_cost

    def _calculate_bound(self, state: SearchState) -> float:
        """
        PRUNING FUNCTION (Optimistic Cost)
        Calculates the "best case" cost from this state.
        """
        current_cost = state.current_cost

        # Calculate minimum cost for works not yet considered
        works_remaining = self.total_works - state.work_index
        total_remaining_space = sum(state.slot_available_space.values())

        future_unassigned_works = max(0, works_remaining - total_remaining_space)

        # This is the "bound": current cost + best possible future cost
        # We assume 0 cost for future days/room-mixes (the optimistic part)
        return current_cost + (future_unassigned_works * self.penalties.unassigned_work)

    def _find_valid_placement(self, work: WorkModel, slot: EventRoomSlotModel, state: SearchState):
        """
        Helper to find the next valid start time, checking ALL constraints.
        """
        track = work.track

        # --- FIX: HARD CONSTRAINT Check Slot/Track Assignment ---
        assigned_track = state.slot_track_map.get(slot.id)
        if assigned_track and assigned_track != track:
            # This slot is already taken by a *different* track.
            # It's impossible to place this work here.
            return None
            # --- End of New Constraint ---

        # Constraint 1: Slot must have work capacity
        if state.slot_available_space[slot.id] <= 0:
            return None

        current_time = state.slot_cursors[slot.id]

        # Loop until we find a valid spot or run out of time
        while True:
            work_start = current_time
            work_end = work_start + self.time_delta

            # Constraint 2: Must fit within slot time boundaries
            if work_end > slot.end:
                return None  # This slot is full (timewise)

            # Constraint 3: Must not overlap with same track (in any room)
            is_conflict = False
            for existing_start, existing_end in state.track_time_usage.get(track, []):
                # Check for overlap: (StartA < EndB) and (EndA > StartB)
                if work_start < existing_end and work_end > existing_start:
                    is_conflict = True
                    current_time = existing_end  # Jump cursor past the conflict
                    break

            if is_conflict:
                continue  # Retry while-loop with new current_time

            # All constraints passed!
            return work_start, work_end

    def _search(self, state: SearchState):
        """
        The recursive core of the Branch and Bound algorithm.
        """

        optimistic_cost_bound = self._calculate_bound(state)
        if optimistic_cost_bound >= self.global_best_cost:
            logger.debug(f"Pruning branch: (Bound {optimistic_cost_bound} >= Best {self.global_best_cost})")
            return

        if state.work_index >= self.total_works:
            # This is a complete solution.
            if state.current_cost < self.global_best_cost:
                logger.info(f"New best solution found! Cost: {state.current_cost}")
                self.global_best_cost = state.current_cost
                self.global_best_solution = list(state.assignments)  # Store copy
            return

        # --- 3. Branching ---
        work_to_try = self.works_to_assign[state.work_index]

        # --- Branch 1: Try to *assign* the work ---
        for room_name in self.sorted_room_names:
            for slot in self.available_slots_by_room[room_name]:

                placement = self._find_valid_placement(work_to_try, slot, state)

                if placement:
                    work_start, work_end = placement

                    # --- Calculate Incremental Cost ---
                    cost_increase = 0
                    day = slot.start.date()

                    is_new_day = day not in state.days_used
                    if is_new_day:
                        cost_increase += self.penalties.per_distinct_day

                    tracks_in_room = state.room_track_map.get(slot.room_name, set())
                    is_new_track_in_room = work_to_try.track not in tracks_in_room
                    is_room_mix = is_new_track_in_room and len(tracks_in_room) > 0
                    if is_room_mix:
                        cost_increase += self.penalties.per_room_track_mix

                    is_new_slot_track = slot.id not in state.slot_track_map

                    # --- Modify State (Move Down the Tree) ---
                    state.work_index += 1
                    state.current_cost += cost_increase
                    state.assignments.append((work_to_try, slot))
                    state.track_time_usage.setdefault(work_to_try.track, []).append((work_start, work_end))

                    old_cursor = state.slot_cursors[slot.id]
                    state.slot_cursors[slot.id] = work_end
                    state.slot_available_space[slot.id] -= 1

                    if is_new_day: state.days_used.add(day)
                    if is_new_track_in_room: state.room_track_map.setdefault(slot.room_name, set()).add(
                        work_to_try.track)
                    if is_new_slot_track:
                        state.slot_track_map[slot.id] = work_to_try.track

                    # --- Recurse ---
                    self._search(state)

                    # --- Backtrack (Revert State / Move Up) ---
                    if is_new_slot_track:
                        del state.slot_track_map[slot.id]
                    if is_new_track_in_room: state.room_track_map[slot.room_name].remove(work_to_try.track)
                    if is_new_day: state.days_used.remove(day)

                    state.slot_available_space[slot.id] += 1
                    state.slot_cursors[slot.id] = old_cursor
                    state.track_time_usage[work_to_try.track].pop()
                    state.assignments.pop()
                    state.current_cost -= cost_increase
                    state.work_index -= 1

        # --- Branch 2: *Skip* this work (do not assign it) ---

        # --- Modify State ---
        state.work_index += 1
        state.current_cost += self.penalties.unassigned_work  # Add the heavy penalty

        # --- Recurse ---
        self._search(state)

        # --- Backtrack ---
        state.current_cost -= self.penalties.unassigned_work
        state.work_index -= 1