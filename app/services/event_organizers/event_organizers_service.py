from uuid import UUID

from app.database.models.member import MemberModel
from app.database.models.user import UserModel
from app.exceptions.members.organizer.organizer_exceptions import AtLeastOneOrganizer, UserNotIsOrganizer
from app.repository.organizers_repository import OrganizerRepository
from app.repository.users_repository import UsersRepository
from app.schemas.members.member_schema import MemberResponseSchema
from app.schemas.users.user import UserSchema
from app.schemas.users.utils import UID
from app.services.services import BaseService


class EventOrganizersService(BaseService):
    def __init__(self, event_id: UUID, organizer_repository: OrganizerRepository, users_repository: UsersRepository):
        self.event_id = event_id
        self.organizer_repository = organizer_repository
        self.users_repository = users_repository

    async def get_all_organizers(self) -> list[MemberResponseSchema]:
        users_organizers = await self.organizer_repository.get_all(self.event_id)
        return list(map(EventOrganizersService.__map_to_schema, users_organizers))

    async def is_organizer(self, user_id: UID) -> bool:
        return await self.organizer_repository.is_member(self.event_id, user_id)

    async def remove_organizer(self, user_id: UID) -> None:
        if not await self.organizer_repository.is_member(self.event_id, user_id):
            raise UserNotIsOrganizer(self.event_id, user_id)
        users_organizers = await self.organizer_repository.get_all(self.event_id)
        if len(users_organizers) <= 1:
            raise AtLeastOneOrganizer(self.event_id, user_id)
        await self.organizer_repository.remove_member(self.event_id, user_id)

    @staticmethod
    def __map_to_schema(model: (UserModel, MemberModel)) -> MemberResponseSchema:
        user, organizer = model
        return MemberResponseSchema(
            event_id=organizer.event_id,
            user_id=organizer.user_id,
            user=UserSchema(email=user.email, name=user.name, lastname=user.lastname),
        )
