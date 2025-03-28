from app.database.models.user import UserRole
from app.exceptions.users_exceptions import (
    EmailAlreadyExists,
    IdAlreadyExists,
)
from app.repository.users_repository import UsersRepository
from app.schemas.users.user import UserModifySchema, UserReply, UserSchema
from app.schemas.users.utils import UID
from app.services.services import BaseService


class UsersService(BaseService):
    def __init__(self, users_repository: UsersRepository, user_id: UID):
        self.users_repository = users_repository
        self.user_id = user_id

    async def exists(self, user_id: UID) -> bool:
        return await self.users_repository.exists(user_id)

    async def create(self, user: UserSchema) -> UID:
        exists = await self.users_repository.exists(self.user_id)
        if exists:
            raise IdAlreadyExists(self.user_id)
        user_id_in_db = await self.users_repository.get_user_id_by_email(user.email)
        if user_id_in_db:
            raise EmailAlreadyExists(user.email)

        user_to_create = UserReply(**user.model_dump(), id=self.user_id, role=UserRole.DEFAULT)

        user_created = await self.users_repository.create(user_to_create)
        return user_created.id

    async def update(self, user: UserModifySchema):
        await self.users_repository.update(self.user_id, user)

    async def get_role(self) -> UserRole:
        return await self.users_repository.get_role(self.user_id)

    async def get(self, user_id: UID) -> UserReply:
        return await self.users_repository.get(user_id)
