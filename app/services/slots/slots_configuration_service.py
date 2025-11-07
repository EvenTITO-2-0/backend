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
from app.services.slots.ConfigurableBBScheduler import CostPenalties, ConfigurableBBScheduler

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

    async def assign_work_to_slot(self, slots_id: int, work_id: UUID):
        logger.info(f"Assigning work {work_id} to slot {slots_id}")
        await self.work_slot_repository.add_work_to_slot_by_id(slots_id, work_id)

    async def delete_all_assignments(self):
        logger.info(f"Deleting all assigned works in event {self.event_id}")
        await self.work_slot_repository.delete_assigned_works_by_event_id(self.event_id)

    async def assign_works_to_slots(self, parameters: AssignWorksParametersSchema):
        """
        (This is your main function from the class 'YourAssignmentService')
        """
        logger.info(f"Starting new optimal assignment with parameters: {parameters}")

        if parameters.reset_previous_assignments:
            logger.info("Resetting previous assignments...")
            await self.delete_all_assignments()

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
            await self.work_slot_repository.add_all(new_links_to_create)
            logger.info("Successfully saved optimal assignments to the database.")

        return {
            "assignments_created": assignments_created,
            "unassigned_works": unassigned_works,
            "final_cost": optimal_cost,
            "is_optimal": True
        }

