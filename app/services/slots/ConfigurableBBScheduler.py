import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Set, Tuple, cast
from uuid import UUID
import copy

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
            unassigned_work=base ** 3, per_distinct_day=base ** same_day_tracks,
            per_room_track_mix=base ** same_room_tracks
        )


@dataclass
class SearchState:
    slot_index: int = 0
    current_cost: float = 0.0
    slot_track_map: Dict[int, str] = field(default_factory=dict)
    track_work_counts_remaining: Dict[str, int] = field(default_factory=dict)
    track_time_usage: Dict[str, List[Tuple[datetime, datetime]]] = field(default_factory=dict)
    days_used: Set[date] = field(default_factory=set)
    room_track_map: Dict[str, Set[str]] = field(default_factory=dict)
    day_track_map: Dict[date, Set[str]] = field(default_factory=dict)


def _has_time_conflict(state: SearchState, track_name: str, slot) -> bool:
    slot_start = cast(datetime, slot.start)
    slot_end = cast(datetime, slot.end)

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
        self._initialize_slots(slots, all_works_map, initial_state, initial_track_counts_remaining, assigned_work_ids)

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
            assigned_work_ids: Set[UUID],
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

            # Store datetimes for precise conflict checking
            start_dt = cast(datetime, slot.start)
            end_dt = cast(datetime, slot.end)
            state.track_time_usage.setdefault(track_name, []).append((start_dt, end_dt))

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
        
        state.day_track_map.setdefault(day, set()).add(track_name)

    def solve(self, greedy_cost_bound=float("inf")):
        logger.info(f"Starting B&B with initial cost bound: {greedy_cost_bound}")

        # 1. Run Greedy to get a better initial bound
        greedy_cost = self._solve_greedy()
        self.global_best_cost = min(greedy_cost, greedy_cost_bound)
        logger.info(f"Greedy initialization complete. Best cost: {self.global_best_cost}")

        # 2. Run Branch and Bound
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

    def _solve_greedy(self) -> float:
        """Runs a quick greedy pass to set a decent upper bound."""
        state = copy.deepcopy(self.initial_state)

        for i in range(self.total_slots):
            slot = self.all_slots[i]
            slot_id = cast(int, slot.id)

            if slot_id in self.slot_pre_assigned_track:
                # Must respect pre-assignment
                track_name = self.slot_pre_assigned_track[slot_id]
                self._apply_greedy_assignment(state, slot, track_name)
                continue

            # Find best candidate
            best_track = None
            """
            Greedy Selection Logic:
            We want to pick a track that 'looks' best. 
            Just checking min_added_cost is a bit short-sighted because it doesn't know about future "spillover" penalties.
            
            Let's sort candidates by our heuristic, then pick the first valid one with lowest immediate cost. 
            """
            candidates = [t for t in self.available_tracks if state.track_work_counts_remaining.get(t, 0) > 0]
            
            room_name = cast(str, slot.room_name)
            current_room_tracks = state.room_track_map.get(room_name, set())
            day = cast(datetime, slot.start).date()
            day_tracks = state.day_track_map.get(day, set())
            
            remaining_day_space = self._get_remaining_day_space(state.slot_index, day)

            def greedy_heuristic_key(track):
                # We want to MAXIMIZE this score
                in_room = track in current_room_tracks
                active_on_day = track in day_tracks
                
                remaining_work = state.track_work_counts_remaining.get(track, 0)
                fits = remaining_work <= remaining_day_space
                
                # Priority:
                # 1. Minimize jumps (In Room)
                # 2. Group by day (Active on Day)
                # 3. If starting new, ensure it fits (Fits)
                return (in_room, active_on_day, fits, remaining_work)

            # Sort descending
            sorted_candidates = sorted(candidates, key=greedy_heuristic_key, reverse=True)
            
            for track in sorted_candidates:
                if _has_time_conflict(state, track, slot):
                    continue
                
                # If we sorted well, the first valid one is likely our best heuristic choice.
                # However, we still check immediate cost to avoid silly local penalties (like room mix if avoidable).
                # Actually, let's trust the heuristic + cost check.
                
                cost_delta = self._calculate_cost_delta(state, slot, track)
                
                # If this track is highly preferred by heuristic (e.g. in_room), we might accept a slightly higher cost?
                # For now, let's keep the simple "min cost" but iterate in heuristic order 
                # and maybe stop early or use heuristic as tie breaker?
                
                # BETTER APPROACH for Greedy: Just pick the top heuristic match that is valid.
                # The heuristic already accounts for "in_room" (which drives cost).
                best_track = track
                min_added_cost = cost_delta # Not used if we break
                break

            if best_track:
                self._apply_greedy_assignment(state, slot, best_track)

        # Calculate final cost
        unassigned_works = sum(state.track_work_counts_remaining.values())
        final_cost = state.current_cost + (unassigned_works * self.penalties.unassigned_work)

        if final_cost < self.global_best_cost:
            self.global_best_cost = final_cost
            self.global_best_solution = dict(state.slot_track_map)

        return final_cost

    def _calculate_cost_delta(self, state, slot, track_name) -> float:
        cost = 0
        day = cast(datetime, slot.start).date()
        if day not in state.days_used:
            cost += self.penalties.per_distinct_day

        room_name = cast(str, slot.room_name)
        tracks_in_room = state.room_track_map.get(room_name, set())
        if track_name not in tracks_in_room and tracks_in_room:
            cost += self.penalties.per_room_track_mix
        return cost
        
    def _get_remaining_day_space(self, current_index: int, current_day: date) -> int:
        """Calculates how much work capacity is left in the current day across all rooms."""
        space = 0
        # Start from current slot (it is not yet filled in the loop context often, but check index usage)
        # In _process_open_slot, state.slot_index points to the CURRENT slot being processed.
        
        for i in range(current_index, self.total_slots):
            slot = self.all_slots[i]
            if cast(datetime, slot.start).date() != current_day:
                break
            # Note: This is an approximation. It counts available space of current + future slots.
            # If we are in recursive Depth First, `available_space` is static per slot, 
            # but we only care about slots we haven't passed yet.
            space += slot.available_space
        return space

    def _apply_greedy_assignment(self, state, slot, track_name):
        works_assigned = min(slot.available_space, state.track_work_counts_remaining[track_name])

        state.current_cost += self._calculate_cost_delta(state, slot, track_name)

        slot_id = cast(int, slot.id)
        state.slot_track_map[slot_id] = track_name

        state.track_work_counts_remaining[track_name] -= works_assigned

        start_dt = cast(datetime, slot.start)
        end_dt = cast(datetime, slot.end)
        state.track_time_usage.setdefault(track_name, []).append((start_dt, end_dt))

        day = start_dt.date()
        state.days_used.add(day)
        room_name = cast(str, slot.room_name)
        state.room_track_map.setdefault(room_name, set()).add(track_name)
        state.day_track_map.setdefault(day, set()).add(track_name)

    def _process_open_slot(self, state: SearchState, slot):
        """Tries all valid tracks for an open slot, then tries skipping the slot."""
        raw_candidates = [t for t in self.available_tracks if state.track_work_counts_remaining.get(t, 0) > 0]

        room_name = cast(str, slot.room_name)
        current_room_tracks = state.room_track_map.get(room_name, set())
        day = cast(datetime, slot.start).date()
        day_tracks = state.day_track_map.get(day, set())
        
        remaining_day_space = self._get_remaining_day_space(state.slot_index, day)

        def heuristic_key(track):
            # 1. Prefer track already in this room (High Locality)
            in_room = track in current_room_tracks
            
            # 2. Prefer track ALREADY active on this day (Group by Date)
            active_on_day = track in day_tracks
            
            remaining_work = state.track_work_counts_remaining.get(track, 0)
            
            # 3. If NOT active on day, prefer tracks that FIT in remaining day space
            # This prevents starting a track that will inevitably spill over to tomorrow.
            fits_in_day = True
            if not active_on_day:
                 fits_in_day = remaining_work <= remaining_day_space

            return (in_room, active_on_day, fits_in_day, remaining_work)

        # Sort descending (True > False, Higher Remaining > Lower)
        tracks_with_work = sorted(raw_candidates, key=heuristic_key, reverse=True)

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

        # Use simple datetime objects for storage
        start_dt = cast(datetime, slot.start)
        end_dt = cast(datetime, slot.end)
        state.track_time_usage.setdefault(track_name, []).append((start_dt, end_dt))

        if is_new_day:
            state.days_used.add(day)
        if is_new_track:
            state.room_track_map.setdefault(room_name, set()).add(track_name)
        
        is_new_day_track = track_name not in state.day_track_map.get(day, set())
        state.day_track_map.setdefault(day, set()).add(track_name)

        self._search(state)

        # Backtrack
        if is_new_day_track:
             state.day_track_map[day].remove(track_name)
             if not state.day_track_map[day]:
                 del state.day_track_map[day]

        if is_new_track:
            state.room_track_map[room_name].remove(track_name)
        if is_new_day:
            state.days_used.remove(day)

        state.track_time_usage[track_name].pop()
        state.track_work_counts_remaining[track_name] += works_assigned
        del state.slot_track_map[slot_id]
        state.slot_index -= 1
        state.current_cost -= cost_increase
