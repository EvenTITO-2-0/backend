from functools import reduce
from itertools import groupby
from operator import attrgetter
from uuid import UUID

from app.database.models.member import MemberModel
from app.database.models.user import UserModel
from app.exceptions.members.member_exceptions import AlreadyMemberExist, MemberRoleNotSupported
from app.exceptions.users_exceptions import UserNotFound
from app.repository.chairs_repository import ChairRepository
from app.repository.organizers_repository import OrganizerRepository
from app.repository.users_repository import UsersRepository
from app.schemas.events.roles import EventRole
from app.schemas.members.member_schema import MemberRequestSchema, MemberResponseWithRolesSchema, RolesRequestSchema
from app.schemas.users.user import UserSchema
from app.schemas.users.utils import UID
from app.services.services import BaseService


class EventMembersService(BaseService):
    def __init__(
        self,
        event_id: UUID,
        organizer_repository: OrganizerRepository,
        chair_repository: ChairRepository,
        users_repository: UsersRepository,
    ):
        self.event_id = event_id
        self.users_repository = users_repository
        self.repositories = {EventRole.ORGANIZER: organizer_repository, EventRole.CHAIR: chair_repository}

    async def get_all_members(self) -> list[MemberResponseWithRolesSchema]:
        result = []
        for role, repository in self.repositories.items():
            members = await repository.get_all(self.event_id)
            result += [EventMembersService.__map_to_schema(x, role) for x in members]

        result.sort(key=attrgetter("user_id"))

        members_response = []
        for _, v in groupby(result, key=attrgetter("user_id")):
            group = list(v)
            roles = list(reduce(lambda x, y: x + y, [x.roles for x in group]))
            member = MemberResponseWithRolesSchema(**({**(group[0].model_dump(mode="json")), "roles": roles}))
            members_response.append(member)
        return members_response

    async def add_member(self, member: MemberRequestSchema) -> UID:
        if member.role not in self.repositories.keys():
            raise MemberRoleNotSupported(member.role)
        user_id = await self.users_repository.get_user_id_by_email(member.email)
        if user_id is None:
            raise UserNotFound(member.email)
        member_repository = self.repositories[member.role]
        if await member_repository.is_member(self.event_id, user_id):
            raise AlreadyMemberExist(self.event_id, user_id, member.role)
        await member_repository.create_member(self.event_id, user_id)
        return user_id

    async def remove_member(self, user_id: UID) -> None:
        for role, repository in self.repositories.items():
            if await repository.is_member(self.event_id, user_id):
                if role == EventRole.ORGANIZER:
                    users_organizers = await repository.get_all(self.event_id)
                    if len(users_organizers) <= 1:
                        continue
                await repository.remove_member(self.event_id, user_id)

    async def update_rol_member(self, user_id: UID, role_schema: RolesRequestSchema):
        for role, repository in self.repositories.items():
            if (role not in role_schema.roles) and (await repository.is_member(self.event_id, user_id)):
                await repository.remove_member(self.event_id, user_id)
            if (role in role_schema.roles) and (not await repository.is_member(self.event_id, user_id)):
                await repository.create_member(self.event_id, user_id)

    @staticmethod
    def __map_to_schema(model: (UserModel, MemberModel), role: EventRole) -> MemberResponseWithRolesSchema:
        user, organizer = model
        return MemberResponseWithRolesSchema(
            event_id=organizer.event_id,
            user_id=organizer.user_id,
            roles=[role],
            user=UserSchema(email=user.email, name=user.name, lastname=user.lastname),
        )
