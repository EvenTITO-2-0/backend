from typing import Annotated

from fastapi import Depends

from app.authorization.admin_user_dep import AdminUsrDep
from app.authorization.caller_id_dep import CallerIdDep
from app.repository.repository import get_repository
from app.repository.users_repository import UsersRepository
from app.services.users.users_admin_service import UsersAdminService


class UsersAdmin:
    async def __call__(
        self,
        user_id: CallerIdDep,
        _: AdminUsrDep,
        users_repository: Annotated[UsersRepository, Depends(get_repository(UsersRepository))],
    ) -> UsersAdminService:
        return UsersAdminService(users_repository, user_id)


users_admin_service = UsersAdmin()
UsersAdminServiceDep = Annotated[UsersAdminService, Depends(users_admin_service)]
