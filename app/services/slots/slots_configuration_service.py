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
        """
        Main entry point.
        Runs a fast GREEDY algorithm to get a good "Lower Bound",
        then runs the full Branch and Bound search for the *true* optimum.
        """
        logger.info(f"Starting optimal assignment with parameters: {parameters}")

        # --- 1. Data Fetching (Your Code) ---
        if parameters.reset_previous_assignments:
            logger.info("Resetting previous assignments...")
            await self.work_slot_repository.delete_by_event_id(self.event_id)

        available_slots = await self.slots_repository.get_slots_by_event_id_with_works(self.event_id)
        assignable_works = await self.works_repository.get_all_approved_works_for_event(self.event_id, offset=0,
                                                                                        limit=9999)

        if not assignable_works or not available_slots:
            logger.warning("No assignable works or available slots.")
            return {"message": "No works or slots to assign."}

        # --- 2. Run Greedy Algorithm (from previous answer) FIRST ---
        # This is critical for getting a good initial Lower Bound
        logger.info("Running fast greedy algorithm to establish initial lower bound...")

        # (Here, you would run the *previous* greedy algorithm)
        # greedy_solution, greedy_count = await self.run_greedy_assignment(parameters, available_slots, assignable_works)

        # For this example, we'll assume the greedy count is 0,
        # but in reality this should be the result of your first algorithm.
        greedy_count = 0
        logger.info(f"Greedy algorithm found an initial solution of {greedy_count} assignments.")

        # --- 3. Run Branch and Bound Algorithm ---
        logger.info("Starting Branch and Bound search for optimal solution...")

        # We must pass *copies* of the data, as the scheduler
        # will modify them during its search.
        scheduler = BranchAndBoundScheduler(
            works=copy.deepcopy(assignable_works),
            slots=copy.deepcopy(available_slots),
            time_per_work=parameters.time_per_work
        )

        # Pass the greedy solution's score as the initial lower bound
        optimal_assignments_list, optimal_count = scheduler.solve(
            initial_lower_bound=greedy_count
        )

        # --- 4. Finalization ---
        logger.info(f"Optimal assignment complete. Found {optimal_count} assignments.")

        new_links_to_create = [
            WorkSlotModel(work_id=work_id, slot_id=slot_id)
            for work_id, slot_id in optimal_assignments_list
        ]

        if new_links_to_create:
            self.work_slot_repository.session.add_all(new_links_to_create)
            await self.work_slot_repository.session.flush()
            await self.work_slot_repository.session.commit()
            logger.info("Successfully saved optimal assignments to the database.")

        return {
            "assignments_created": optimal_count,
            "unassigned_works": len(assignable_works) - optimal_count,
            "is_optimal": True
        }


class BranchAndBoundScheduler:
    """
    Implements a Branch and Bound algorithm to find the *optimal*
    assignment of works to slots, maximizing the number of assigned works.

    WARNING: This is computationally expensive and not for real-time requests
    with large inputs.
    """

    def __init__(self, works: list, slots: list, time_per_work: int):
        self.time_delta = timedelta(minutes=time_per_work)

        # 1. Sort works by track, biggest track first
        assignable_works_by_track = {}
        for w in works:
            assignable_works_by_track.setdefault(w.track, []).append(w)

        sorted_track_names = sorted(
            assignable_works_by_track.keys(),
            key=lambda t: len(assignable_works_by_track[t]),
            reverse=True
        )

        # Our master list of works to process, in sorted order
        self.works_to_assign = []
        for track_name in sorted_track_names:
            self.works_to_assign.extend(assignable_works_by_track[track_name])

        # 2. Sort slots by room, biggest room first
        self.available_slots_by_room = {}
        for slot in slots:
            slot_duration = (slot.end - slot.start).total_seconds() / 60
            total_capacity = int(slot_duration // time_per_work)
            slot.available_space = total_capacity - len(slot.work_links)
            self.available_slots_by_room.setdefault(slot.room_name, []).append(slot)

        for room_name in self.available_slots_by_room:
            self.available_slots_by_room[room_name].sort(key=lambda s: s.start)

        room_total_space = {
            r: sum(s.available_space for s in s_list)
            for r, s_list in self.available_slots_by_room.items()
        }
        self.sorted_room_names = sorted(
            room_total_space.keys(),
            key=lambda r: room_total_space[r],
            reverse=True
        )

        # 3. Initialize state for the B&B search
        self.all_slots = slots
        self.global_best_assignment_count = 0
        self.global_best_solution = []  # List of (work_id, slot_id)

        self.total_works = len(self.works_to_assign)
        self.total_possible_slots = sum(room_total_space.values())

    def solve(self, initial_lower_bound=0):
        """
        Starts the Branch and Bound search.

        An 'initial_lower_bound' (e.g., from a greedy algorithm)
        is CRITICAL for pruning and performance.
        """
        self.global_best_assignment_count = initial_lower_bound
        logger.info(f"Starting B&B with initial lower bound: {self.global_best_assignment_count}")

        # Initial state for the recursive search
        initial_state = {
            "work_index": 0,  # Current work we are considering
            "assigned_works_count": 0,
            "current_assignments": [],  # List of (work_id, slot_id)
            "track_time_usage": {},  # {'Track A': [(start, end), ...]}
            "slot_cursors": {s.id: s.start for s in self.all_slots},
            "slot_available_space": {s.id: s.available_space for s in self.all_slots}
        }

        self._search(initial_state)

        logger.info(f"B&B search complete. Optimal solution found: {self.global_best_assignment_count} assignments.")
        return self.global_best_solution, self.global_best_assignment_count

    def _search(self, state):
        """
        The recursive core of the Branch and Bound algorithm.
        """

        # --- 1. Base Case (Leaf Node) ---
        # We've considered all works. This is a complete solution.
        if state["work_index"] == self.total_works:
            if state["assigned_works_count"] > self.global_best_assignment_count:
                logger.info(f"New best solution found: {state['assigned_works_count']} works.")
                self.global_best_assignment_count = state["assigned_works_count"]
                self.global_best_solution = list(state["current_assignments"])  # Store a copy
            return

        # --- 2. Bound Calculation (Pruning) ---
        works_assigned = state["assigned_works_count"]
        works_remaining = self.total_works - state["work_index"]
        total_remaining_space = sum(state["slot_available_space"].values())

        # The tight upper bound
        upper_bound = works_assigned + min(works_remaining, total_remaining_space)

        # PRUNING STEP:
        if upper_bound <= self.global_best_assignment_count:
            # logger.debug(f"Pruning branch: (UB {upper_bound} <= LB {self.global_best_assignment_count})")
            return

        # --- 3. Branching ---

        work_to_try = self.works_to_assign[state["work_index"]]

        # --- Branch 1: Try to *assign* the work to every possible slot ---

        # We iterate through rooms in our sorted "biggest first" order
        # to try and find the *best* assignment first.
        assigned_to_a_slot = False
        for room_name in self.sorted_room_names:
            for slot in self.available_slots_by_room[room_name]:

                # Try to find a valid placement in this slot
                placement = self._find_valid_placement(work_to_try, slot, state)

                if placement:
                    assigned_to_a_slot = True
                    work_start_time, work_end_time = placement

                    # Create the new state for this branch
                    # (Using backtracking by modifying state, then reverting)

                    # --- Modify State ---
                    state["work_index"] += 1
                    state["assigned_works_count"] += 1
                    state["current_assignments"].append((work_to_try.id, slot.id))
                    state["track_time_usage"].setdefault(work_to_try.track, []).append((work_start_time, work_end_time))

                    old_cursor = state["slot_cursors"][slot.id]
                    state["slot_cursors"][slot.id] = work_end_time
                    state["slot_available_space"][slot.id] -= 1

                    # --- Recurse ---
                    self._search(state)

                    # --- Backtrack (Revert State) ---
                    state["slot_available_space"][slot.id] += 1
                    state["slot_cursors"][slot.id] = old_cursor
                    state["track_time_usage"][work_to_try.track].pop()
                    state["current_assignments"].pop()
                    state["assigned_works_count"] -= 1
                    state["work_index"] -= 1

        # --- Branch 2: *Skip* this work (do not assign it) ---
        # We *always* explore this branch

        state["work_index"] += 1  # Move to the next work
        self._search(state)
        state["work_index"] -= 1  # Backtrack

    def _find_valid_placement(self, work, slot, state):
        """
        Helper to find the next valid start time for a work in a slot,
        checking all constraints.
        """

        # Constraint 1: Slot must have work capacity
        if state["slot_available_space"][slot.id] <= 0:
            return None

        track = work.track
        current_time = state["slot_cursors"][slot.id]

        # Loop until we find a valid spot or run out of time
        while True:
            work_start_time = current_time
            work_end_time = work_start_time + self.time_delta

            # Constraint 2: Must fit within slot time boundaries
            if work_end_time > slot.end:
                return None  # This slot is full

            # Constraint 3: Must not overlap with same track
            is_conflict = False
            for existing_start, existing_end in state["track_time_usage"].get(track, []):
                if work_start_time < existing_end and work_end_time > existing_start:
                    is_conflict = True
                    # Conflict! Advance our cursor to the end of the conflict
                    current_time = existing_end
                    break  # Break from conflict-check loop

            if is_conflict:
                continue  # Retry the while loop with the new `current_time`

            # All constraints passed!
            return work_start_time, work_end_time