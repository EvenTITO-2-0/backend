import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Set, Tuple, cast
from uuid import UUID

from app.database.models import EventRoomSlotModel, WorkModel

logger = logging.getLogger(__name__)


@dataclass
class CostPenalties:
    unassigned_work: int = 10000
    per_distinct_day: int = 100
    per_room_track_mix: int = 10

    @classmethod
    def from_params(cls, same_day_tracks: int, same_room_tracks: int):
        base = 4
        return cls(
            unassigned_work=base**3,
            per_distinct_day=base**same_day_tracks,
            per_room_track_mix=base**same_room_tracks
        )


@dataclass
class SearchState:
    slot_index: int = 0
    current_cost: float = 0.0
    slot_track_map: Dict[int, str] = field(default_factory=dict)
    track_work_counts_remaining: Dict[str, int] = field(default_factory=dict)
    track_time_usage: Dict[str, List[Tuple[date, date]]] = field(default_factory=dict)
    days_used: Set[date] = field(default_factory=set)
    room_track_map: Dict[str, Set[str]] = field(default_factory=dict)


def _has_time_conflict(state: SearchState, track_name: str, slot) -> bool:
    # Use .date() to compare dates, not datetimes
    slot_start = cast(datetime, slot.start).date()
    slot_end = cast(datetime, slot.end).date()

    for existing_start, existing_end in state.track_time_usage.get(track_name, []):
        if slot_start < existing_end and slot_end > existing_start:
            return True
    return False


class ConfigurableBBScheduler:
    def __init__(
            self, works: List[WorkModel], slots: List[EventRoomSlotModel], time_per_work: int, penalties: CostPenalties
    ):
        self.penalties = penalties
        self.time_delta = timedelta(minutes=time_per_work)
        self.time_per_work = time_per_work

        # FIX 1: Map keys are UUIDs, not ints
        all_works_map: Dict[UUID, WorkModel] = {cast(UUID, w.id): w for w in works}

        self.slot_pre_assigned_track: Dict[int, str] = {}
        assigned_work_ids: Set[UUID] = set()

        initial_state = SearchState()

        # Group works by track
        all_works_by_track: Dict[str, List[WorkModel]] = {}
        for w in works:
            # FIX 2: Cast Column[str] to str
            track_name = cast(str, w.track)
            all_works_by_track.setdefault(track_name, []).append(w)

        initial_track_counts_remaining: Dict[str, int] = {
            track: len(works_list) for track, works_list in all_works_by_track.items()
        }

        # Delegate slot initialization
        self._initialize_slots(
            slots,
            all_works_map,
            initial_state,
            initial_track_counts_remaining,
            assigned_work_ids
        )

        unassigned_works = [w for w in works if cast(UUID, w.id) not in assigned_work_ids]

        self.works_by_track: Dict[str, List[WorkModel]] = {}
        for w in unassigned_works:
            track_name = cast(str, w.track)
            self.works_by_track.setdefault(track_name, []).append(w)

        self.track_counts: Dict[str, int] = {
            track: len(works_list) for track, works_list in self.works_by_track.items()
        }
        self.total_works = len(unassigned_works)
        self.available_tracks = list(self.track_counts.keys())

        logger.info(f"Scheduler initialized. Total unassigned works to place: {self.total_works}")

        self.all_slots: List[EventRoomSlotModel] = sorted(slots, key=lambda s: (s.start, s.room_name))

        # FIX 3: Cast Column[int] to int for Slot IDs
        self.slot_map: Dict[int, EventRoomSlotModel] = {cast(int, s.id): s for s in self.all_slots}
        self.total_slots = len(self.all_slots)

        self.global_best_cost = float("inf")
        self.global_best_solution: Dict[int, str] = {}
        self.initial_state = initial_state
        self.initial_state.track_work_counts_remaining = initial_track_counts_remaining

    def _initialize_slots(
            self,
            slots: List[EventRoomSlotModel],
            all_works_map: Dict[UUID, WorkModel],
            state: SearchState,
            track_counts: Dict[str, int],
            assigned_work_ids: Set[UUID]
    ):
        """Helper to process slots and pre-assignments during init."""
        for slot in slots:
            slot_duration = (slot.end - slot.start).total_seconds() / 60
            slot.total_capacity = int(slot_duration // self.time_per_work)
            num_existing_works = len(slot.work_links)
            slot.available_space = slot.total_capacity - num_existing_works

            if num_existing_works > 0:
                self._handle_slot_pre_assignment(
                    slot, all_works_map, state, track_counts, assigned_work_ids, num_existing_works
                )

    def _handle_slot_pre_assignment(
            self, slot, works_map: Dict[UUID, WorkModel], state, track_counts, assigned_ids: Set[UUID], num_existing
    ):
        try:
            first_work_id = slot.work_links[0].work_id
            first_work = works_map.get(first_work_id)

            if not first_work:
                logger.warning(f"Could not find work {first_work_id} for slot {slot.id}")
                return

            track_name = cast(str, first_work.track)
            slot_id = cast(int, slot.id)

            self.slot_pre_assigned_track[slot_id] = track_name

            for link in slot.work_links:
                assigned_ids.add(link.work_id)

            track_counts[track_name] -= num_existing
            state.slot_track_map[slot_id] = track_name

            # FIX 4: Use dates instead of datetime columns
            start_date = cast(datetime, slot.start).date()
            end_date = cast(datetime, slot.end).date()
            state.track_time_usage.setdefault(track_name, []).append((start_date, end_date))

            self._apply_cost_for_assignment(state, slot, track_name)

        except (IndexError, AttributeError):
            logger.error(f"Slot {slot.id} has malformed work links.", exc_info=True)

    def _apply_cost_for_assignment(self, state, slot, track_name):
        """Updates state cost and sets for day/room usage."""
        day = cast(datetime, slot.start).date()
        if day not in state.days_used:
            state.days_used.add(day)
            state.current_cost += self.penalties.per_distinct_day

        room_name = cast(str, slot.room_name)
        tracks_in_room = state.room_track_map.get(room_name, set())
        if track_name not in tracks_in_room:
            if tracks_in_room:
                state.current_cost += self.penalties.per_room_track_mix
            state.room_track_map.setdefault(room_name, set()).add(track_name)

    def solve(self, greedy_cost_bound=float("inf")):
        logger.info(f"Starting B&B with initial cost bound: {greedy_cost_bound}")
        self.global_best_cost = greedy_cost_bound
        self._search(self.initial_state)
        logger.info(f"B&B search complete. Optimal cost found: {self.global_best_cost}")

        final_work_assignments = []
        works_map_copy = {track: list(works) for track, works in self.works_by_track.items()}

        for slot_id, track_name in self.global_best_solution.items():
            slot = self.slot_map[slot_id]
            for _ in range(slot.available_space):
                if works_map_copy.get(track_name):
                    work_obj = works_map_copy[track_name].pop()
                    final_work_assignments.append((work_obj, slot))
                else:
                    break
        return final_work_assignments, self.global_best_cost

    def _calculate_bound(self, state: SearchState) -> float:
        current_cost = state.current_cost
        works_still_needed = sum(state.track_work_counts_remaining.values())

        total_remaining_space = 0
        for i in range(state.slot_index, self.total_slots):
            total_remaining_space += self.all_slots[i].available_space

        future_unassigned_works = max(0, works_still_needed - total_remaining_space)
        return current_cost + (future_unassigned_works * self.penalties.unassigned_work)

    def _search(self, state: SearchState):
        if state.slot_index >= self.total_slots:
            self._update_best_solution(state)
            return

        if self._calculate_bound(state) >= self.global_best_cost:
            return

        slot_to_try = self.all_slots[state.slot_index]
        slot_id = cast(int, slot_to_try.id)
        pre_assigned_track = self.slot_pre_assigned_track.get(slot_id)

        if pre_assigned_track:
            self._process_pre_assigned_slot(state, slot_to_try, pre_assigned_track)
        else:
            self._process_open_slot(state, slot_to_try)

    def _update_best_solution(self, state: SearchState):
        unassigned_works = sum(state.track_work_counts_remaining.values())
        final_cost = state.current_cost + (unassigned_works * self.penalties.unassigned_work)

        if final_cost < self.global_best_cost:
            logger.info(f"New best solution found! Cost: {final_cost}")
            self.global_best_cost = final_cost
            self.global_best_solution = dict(state.slot_track_map)

    def _process_pre_assigned_slot(self, state: SearchState, slot, track_name: str):
        """Handles recursion for a slot that already has a track locked."""
        remaining = state.track_work_counts_remaining.get(track_name, 0)
        works_to_assign = 0

        if remaining > 0 and slot.available_space > 0:
            works_to_assign = min(slot.available_space, remaining)
            state.track_work_counts_remaining[track_name] -= works_to_assign

        state.slot_index += 1
        self._search(state)
        state.slot_index -= 1

        if works_to_assign > 0:
            state.track_work_counts_remaining[track_name] += works_to_assign

    def _process_open_slot(self, state: SearchState, slot):
        """Tries all valid tracks for an open slot, then tries skipping the slot."""
        tracks_with_work = [
            t for t in self.available_tracks if state.track_work_counts_remaining.get(t, 0) > 0
        ]

        for track_name in tracks_with_work:
            if _has_time_conflict(state, track_name, slot):
                continue

            self._assign_track_and_recurse(state, slot, track_name)

        # Option: Leave slot empty for now (skip)
        state.slot_index += 1
        self._search(state)
        state.slot_index -= 1

    def _assign_track_and_recurse(self, state: SearchState, slot, track_name: str):
        works_assigned = min(slot.available_space, state.track_work_counts_remaining[track_name])

        # Calculate Deltas
        cost_increase = 0
        day = cast(datetime, slot.start).date()
        is_new_day = day not in state.days_used

        room_name = cast(str, slot.room_name)
        tracks_in_room = state.room_track_map.get(room_name, set())
        is_new_track = track_name not in tracks_in_room
        is_mix = is_new_track and len(tracks_in_room) > 0

        if is_new_day:
            cost_increase += self.penalties.per_distinct_day
        if is_mix:
            cost_increase += self.penalties.per_room_track_mix

        # Apply State Changes
        state.current_cost += cost_increase
        state.slot_index += 1

        slot_id = cast(int, slot.id)
        state.slot_track_map[slot_id] = track_name

        state.track_work_counts_remaining[track_name] -= works_assigned

        # Use simple date objects for storage
        start_date = cast(datetime, slot.start).date()
        end_date = cast(datetime, slot.end).date()
        state.track_time_usage.setdefault(track_name, []).append((start_date, end_date))

        if is_new_day:
            state.days_used.add(day)
        if is_new_track:
            state.room_track_map.setdefault(room_name, set()).add(track_name)

        self._search(state)

        # Backtrack
        if is_new_track:
            state.room_track_map[room_name].remove(track_name)
        if is_new_day:
            state.days_used.remove(day)

        state.track_time_usage[track_name].pop()
        state.track_work_counts_remaining[track_name] += works_assigned
        del state.slot_track_map[slot_id]
        state.slot_index -= 1
        state.current_cost -= cost_increase
