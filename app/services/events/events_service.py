from uuid import UUID

from app.database.models.event import EventStatus
from app.database.models.user import UserRole
from app.exceptions.events_exceptions import EventNotFound, InvalidEventSameTitle, InvalidQueryEventNotCreatedNotAdmin
from app.repository.events_repository import EventsRepository
from app.schemas.events.configuration import EventConfigurationSchema
from app.schemas.events.create_event import CreateEventSchema
from app.schemas.events.public_event_with_roles import PublicEventWithRolesSchema
from app.schemas.users.utils import UID
from app.services.event_organizers.event_organizers_service import EventOrganizersService
from app.services.notifications.events_notifications_service import EventsNotificationsService
from app.services.services import BaseService


class EventsService(BaseService):
    def __init__(
        self,
        events_repository: EventsRepository,
        organizers_service: EventOrganizersService,
        event_notification_service: EventsNotificationsService,
    ):
        self.events_repository = events_repository
        self.organizers_service = organizers_service
        self.event_notification_service = event_notification_service

    async def create(self, event: CreateEventSchema, creator_id: UID, user_role: UserRole):
        event_same_title_exists = await self.events_repository.event_with_title_exists(event.title)
        if event_same_title_exists:
            raise InvalidEventSameTitle(event.title)

        if user_role in [UserRole.EVENT_CREATOR, UserRole.ADMIN]:
            status = EventStatus.CREATED
        else:
            status = EventStatus.WAITING_APPROVAL

        event = EventConfigurationSchema(**event.model_dump(mode="json"), status=status)
        event_created = await self.events_repository.create(creator_id, event)

        # Notify waiting approval event to creator event
        if status.value == EventStatus.WAITING_APPROVAL.value:
            await self.event_notification_service.notify_event_waiting_approval(event_created)
        elif status.value == EventStatus.CREATED.value:
            await self.event_notification_service.notify_event_created(event_created)

        return event_created.id

    async def get_my_events(self, caller_id: UID, offset: int, limit: int) -> list[PublicEventWithRolesSchema]:
        return await self.events_repository.get_all_events_for_user(caller_id, offset=offset, limit=limit)

    async def get_all_events(
        self, offset: int, limit: int, status: EventStatus | None, title_search: str | None, user_role: UserRole
    ):
        if status != EventStatus.STARTED and user_role != UserRole.ADMIN:
            raise InvalidQueryEventNotCreatedNotAdmin(status, user_role)
        events = await self.events_repository.get_all_events(offset, limit, status, title_search)
        if user_role != UserRole.ADMIN:
            for event in events:
                event.creator = None
        return events

    async def get_public_event(self, caller_id: UID | None, event_id: UUID) -> PublicEventWithRolesSchema:
        event = await self.events_repository.get(event_id)
        if event is None:
            raise EventNotFound(event_id)
        event = PublicEventWithRolesSchema.model_validate(event)
        if caller_id is None:
            return event
        event_roles = await self.events_repository.get_roles(event_id, caller_id)
        event.roles = event_roles
        return event
