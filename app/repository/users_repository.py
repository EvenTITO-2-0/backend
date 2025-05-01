from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import UserModel, UserRole
from app.exceptions.users_exceptions import UserWithEmailNotFound
from app.repository.crud_repository import Repository
from app.schemas.users.user import UserSchema
from app.schemas.users.utils import UID


class UsersRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel)

    async def get_admin_users(self) -> list[UserModel]:
        conditions = [UserModel.role == UserRole.ADMIN.value]

        return await self._get_many_with_conditions(conditions, 0, 100)

    async def get_amount_admins(self):
        admin_role = UserRole.ADMIN.value
        conditions = [UserModel.role == admin_role]
        return await self._count_with_conditions(conditions)

    async def get_user_id_by_email(self, email):
        conditions = [UserModel.email == email]
        user = await self._get_with_conditions(conditions)  # TODO: change to get only ID.
        if user is None:
            return user
        return user.id

    async def get_user_by_email(self, email):
        conditions = [UserModel.email == email]
        user = await self._get_with_conditions(conditions)
        if user is None:
            raise UserWithEmailNotFound(email)
        return user

    async def create_user(self, id, user: UserSchema):
        db_user = UserModel(**user.model_dump(), id=id)
        return await self.create(db_user)

    async def get_role(self, id: UID) -> UserRole:
        conditions = self._primary_key_conditions(id)
        return await self._get_with_values(conditions, UserModel.role)
