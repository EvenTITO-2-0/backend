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
    Holds the state for a slot-centric decision tree.
    """
    slot_index: int = 0
    current_cost: float = 0.0
    slot_track_map: Dict[int, str] = field(default_factory=dict)
    track_work_counts_remaining: Dict[str, int] = field(default_factory=dict)
    track_time_usage: Dict[str, List[Tuple[date, date]]] = field(default_factory=dict)
    days_used: Set[date] = field(default_factory=set)
    room_track_map: Dict[str, Set[str]] = field(default_factory=dict)


class ConfigurableBBScheduler:
    """
    A Branch and Bound scheduler that decides which track
    to assign to each slot.

    MODIFIED: This scheduler now accounts for slots that have pre-existing
    work assignments. It will "lock" those slots to their assigned
    track and only attempt to fill their remaining capacity.
    """

    def __init__(self, works: List[WorkModel], slots: List[EventRoomSlotModel],
                 time_per_work: int, penalties: CostPenalties):

        self.penalties = penalties
        self.time_delta = timedelta(minutes=time_per_work)

        all_works_map: Dict[int, WorkModel] = {w.id: w for w in works}

        self.slot_pre_assigned_track: Dict[int, str] = {}
        assigned_work_ids: Set[int] = set()

        initial_state = SearchState()

        all_works_by_track: Dict[str, List[WorkModel]] = {}
        for w in works:
            all_works_by_track.setdefault(w.track, []).append(w)

        initial_track_counts_remaining: Dict[str, int] = {
            track: len(works_list)
            for track, works_list in all_works_by_track.items()
        }

        for slot in slots:
            slot_duration = (slot.end - slot.start).total_seconds() / 60
            slot.total_capacity = int(slot_duration // time_per_work)

            num_existing_works = len(slot.work_links)

            slot.available_space = slot.total_capacity - num_existing_works

            if num_existing_works > 0:
                try:
                    first_work_id = slot.work_links[0].work_id
                    first_work = all_works_map.get(first_work_id)

                    if first_work:
                        track_name = first_work.track
                        self.slot_pre_assigned_track[slot.id] = track_name

                        for link in slot.work_links:
                            assigned_work_ids.add(link.work_id)

                        initial_track_counts_remaining[track_name] -= num_existing_works

                        initial_state.slot_track_map[slot.id] = track_name

                        initial_state.track_time_usage.setdefault(track_name, []).append((slot.start, slot.end))

                        day = slot.start.date()
                        is_new_day = day not in initial_state.days_used
                        if is_new_day:
                            initial_state.days_used.add(day)
                            initial_state.current_cost += self.penalties.per_distinct_day

                        tracks_in_room = initial_state.room_track_map.get(slot.room_name, set())
                        is_new_track_in_room = track_name not in tracks_in_room
                        if is_new_track_in_room:
                            if tracks_in_room:  # Room mix only if it's the 2nd+ track
                                initial_state.current_cost += self.penalties.per_room_track_mix
                            initial_state.room_track_map.setdefault(slot.room_name, set()).add(track_name)

                    else:
                        logger.warning(f"Could not find work with ID {first_work_id} for pre-assigned slot {slot.id}")

                except (IndexError, AttributeError):
                    logger.error(f"Slot {slot.id} has work_links but data is malformed.", exc_info=True)

        unassigned_works = [w for w in works if w.id not in assigned_work_ids]

        self.works_by_track: Dict[str, List[WorkModel]] = {}
        for w in unassigned_works:
            self.works_by_track.setdefault(w.track, []).append(w)

        self.track_counts: Dict[str, int] = {
            track: len(works_list)
            for track, works_list in self.works_by_track.items()
        }
        self.total_works = len(unassigned_works)
        self.available_tracks = list(self.track_counts.keys())

        logger.info(f"Scheduler initialized. Total unassigned works to place: {self.total_works}")
        logger.info(f"Initial cost from pre-assignments: {initial_state.current_cost}")

        self.all_slots: List[EventRoomSlotModel] = sorted(slots, key=lambda s: (s.start, s.room_name))
        self.slot_map: Dict[int, EventRoomSlotModel] = {s.id: s for s in self.all_slots}
        self.total_slots = len(self.all_slots)

        self.global_best_cost = float('inf')
        self.global_best_solution: Dict[int, str] = {}
        self.initial_state = initial_state
        self.initial_state.track_work_counts_remaining = initial_track_counts_remaining

    def solve(self, greedy_cost_bound=float('inf')):
        """
        Starts the B&B search.
        """
        logger.info(f"Starting B&B with initial cost bound: {greedy_cost_bound}")
        self.global_best_cost = greedy_cost_bound

        self._search(self.initial_state)

        logger.info(f"B&B search complete. Optimal cost found: {self.global_best_cost}")

        final_work_assignments = []
        works_map_copy = {track: list(works) for track, works in self.works_by_track.items()}

        for slot_id, track_name in self.global_best_solution.items():
            slot = self.slot_map[slot_id]
            works_to_place_in_slot = slot.available_space

            for _ in range(works_to_place_in_slot):
                if works_map_copy.get(track_name):
                    work_obj = works_map_copy[track_name].pop()
                    final_work_assignments.append((work_obj, slot))
                else:
                    break

        return final_work_assignments, self.global_best_cost

    def _calculate_bound(self, state: SearchState) -> float:
        """
        PRUNING FUNCTION (Optimistic Cost)
        Calculates the "best case" cost from this state.
        """
        current_cost = state.current_cost

        works_still_needed = sum(state.track_work_counts_remaining.values())

        total_remaining_space = 0
        for i in range(state.slot_index, self.total_slots):
            slot = self.all_slots[i]
            pre_assigned_track = self.slot_pre_assigned_track.get(slot.id)
            if not pre_assigned_track:
                total_remaining_space += slot.available_space
            else:
                total_remaining_space += slot.available_space

        # O mas simple
        # for i in range(state.slot_index, self.total_slots):
        #     total_remaining_space += self.all_slots[i].available_space

        future_unassigned_works = max(0, works_still_needed - total_remaining_space)

        return current_cost + (future_unassigned_works * self.penalties.unassigned_work)

    def _search(self, state: SearchState):
        """
        The recursive core of the Branch and Bound algorithm.
        Decides which track to assign to the slot at `state.slot_index`.
        """

        if state.slot_index >= self.total_slots:
            unassigned_works = sum(state.track_work_counts_remaining.values())
            final_cost = state.current_cost + (unassigned_works * self.penalties.unassigned_work)

            if final_cost < self.global_best_cost:
                logger.info(f"New best solution found! Cost: {final_cost}")
                self.global_best_cost = final_cost
                self.global_best_solution = dict(state.slot_track_map)
            return

        optimistic_cost_bound = self._calculate_bound(state)
        if optimistic_cost_bound >= self.global_best_cost:
            return

        slot_to_try = self.all_slots[state.slot_index]

        pre_assigned_track = self.slot_pre_assigned_track.get(slot_to_try.id)

        if pre_assigned_track:
            track_name = pre_assigned_track
            works_to_assign = 0

            if state.track_work_counts_remaining.get(track_name, 0) > 0 and slot_to_try.available_space > 0:

                works_to_assign = min(slot_to_try.available_space, state.track_work_counts_remaining[track_name])

                state.slot_index += 1
                state.track_work_counts_remaining[track_name] -= works_to_assign

                self._search(state)
                state.track_work_counts_remaining[track_name] += works_to_assign
                state.slot_index -= 1

            else:
                state.slot_index += 1
                self._search(state)
                state.slot_index -= 1

        else:
            tracks_with_remaining_works = [
                t for t in self.available_tracks
                if state.track_work_counts_remaining.get(t, 0) > 0
            ]

            for track_name in tracks_with_remaining_works:

                is_conflict = False
                for existing_start, existing_end in state.track_time_usage.get(track_name, []):
                    if slot_to_try.start < existing_end and slot_to_try.end > existing_start:
                        is_conflict = True
                        break

                if is_conflict:
                    continue

                works_this_slot_can_take = slot_to_try.available_space

                works_this_track_needs = state.track_work_counts_remaining[track_name]
                works_to_assign = min(works_this_slot_can_take, works_this_track_needs)

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

                state.slot_index += 1
                state.current_cost += cost_increase
                state.slot_track_map[slot_to_try.id] = track_name
                state.track_work_counts_remaining[track_name] -= works_to_assign
                state.track_time_usage.setdefault(track_name, []).append((slot_to_try.start, slot_to_try.end))

                if is_new_day: state.days_used.add(day)
                if is_new_track_in_room: state.room_track_map.setdefault(slot_to_try.room_name, set()).add(track_name)

                self._search(state)

                if is_new_track_in_room: state.room_track_map[slot_to_try.room_name].remove(track_name)
                if is_new_day: state.days_used.remove(day)

                state.track_time_usage[track_name].pop()
                state.track_work_counts_remaining[track_name] += works_to_assign
                del state.slot_track_map[slot_to_try.id]
                state.current_cost -= cost_increase
                state.slot_index -= 1

            state.slot_index += 1
            self._search(state)
            state.slot_index -= 1
