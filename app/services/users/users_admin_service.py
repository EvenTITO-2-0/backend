from app.database.models.user import UserRole
from app.exceptions.users_exceptions import CantRemoveLastAdmin, UserNotFound
from app.repository.users_repository import UsersRepository
from app.schemas.users.user import UserReply
from app.schemas.users.user_role import UserRoleSchema
from app.schemas.users.utils import UID
from app.services.services import BaseService


class UsersAdminService(BaseService):
    def __init__(self, users_repository: UsersRepository, user_id: UID):
        self.users_repository = users_repository
        self.admin_id = user_id

    async def update_role(self, user_id: UID, new_role: UserRoleSchema):
        await self.__validate_always_at_least_one_admin(user_id, new_role)
        if not await self.users_repository.update(user_id, new_role):
            raise UserNotFound(user_id)

    async def __validate_always_at_least_one_admin(self, user_id: UID, role):
        """
        One can remove himself from Admin role, but there must be
        always at least one admin.
        """
        if (
            (self.admin_id == user_id)
            and (role != UserRole.ADMIN)
            and (await self.users_repository.get_amount_admins() == 1)
        ):
            raise CantRemoveLastAdmin()

    async def get_many(self, offset: int, limit: int) -> list[UserReply]:
        return await self.users_repository.get_many(offset, limit)
