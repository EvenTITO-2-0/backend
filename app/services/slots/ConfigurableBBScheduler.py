import copy
import logging
from dataclasses import dataclass, field
from datetime import timedelta, date
from typing import Set, Dict, List, Tuple

from app.database.models import WorkModel, EventRoomSlotModel

logger = logging.getLogger(__name__)

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