from uuid import UUID

from app.database.models.chair import ChairModel
from app.database.models.user import UserModel
from app.exceptions.members.chair.chair_exceptions import InvalidUpdateTrack, UserNotIsChair
from app.repository.chairs_repository import ChairRepository
from app.repository.users_repository import UsersRepository
from app.schemas.events.schemas import DynamicTracksEventSchema
from app.schemas.members.chair_schema import ChairResponseSchema
from app.schemas.users.user import UserSchema
from app.schemas.users.utils import UID
from app.services.events.events_configuration_service import EventsConfigurationService
from app.services.services import BaseService


class EventChairService(BaseService):
    def __init__(
        self,
        event_id: UUID,
        events_configuration_service: EventsConfigurationService,
        chair_repository: ChairRepository,
        users_repository: UsersRepository,
    ):
        self.event_id = event_id
        self.events_configuration_service = events_configuration_service
        self.chair_repository = chair_repository
        self.users_repository = users_repository

    async def get_all_chairs(self):
        users_chairs = await self.chair_repository.get_all(self.event_id)
        return list(map(EventChairService.__map_to_schema, users_chairs))

    async def get_chair(self, user_id: UID):
        if not await self.chair_repository.is_member(self.event_id, user_id):
            raise UserNotIsChair(self.event_id, user_id)
        chair = await self.chair_repository.get_member(self.event_id, user_id)
        return EventChairService.__map_to_schema(chair)

    async def remove_chair(self, user_id: UID) -> None:
        if not await self.chair_repository.is_member(self.event_id, user_id):
            raise UserNotIsChair(self.event_id, user_id)
        await self.chair_repository.remove_member(self.event_id, user_id)

    async def is_chair(self, user_id: UID) -> bool:
        return await self.chair_repository.is_member(self.event_id, user_id)

    async def update_tracks(self, user_id: UID, tracks_schema: DynamicTracksEventSchema) -> None:
        if not await self.chair_repository.is_member(self.event_id, user_id):
            raise UserNotIsChair(self.event_id, user_id)
        event_tracks = await self.events_configuration_service.get_event_tracks()
        valid_tracks = []
        for new_track in tracks_schema.tracks:
            if new_track not in event_tracks:
                raise InvalidUpdateTrack(self.event_id, new_track, tracks_schema.tracks)
            valid_tracks.append(new_track)
        await self.chair_repository.update_tracks(self.event_id, user_id, valid_tracks)

    @staticmethod
    def __map_to_schema(model: tuple[UserModel, ChairModel]) -> ChairResponseSchema:
        user, chair = model
        tracks = chair.tracks if chair.tracks else []
        return ChairResponseSchema(
            event_id=chair.event_id,
            user_id=chair.user_id,
            tracks=tracks,
            user=UserSchema(email=user.email, name=user.name, lastname=user.lastname),
        )
