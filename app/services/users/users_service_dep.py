from typing import Annotated

from fastapi import Depends

from app.authorization.caller_id_dep import CallerIdDep
from app.repository.repository import get_repository
from app.repository.users_repository import UsersRepository
from app.services.users.users_service import UsersService


class UsersDependencyChecker:
    async def __call__(
        self,
        caller_id: CallerIdDep,
        users_repository: Annotated[UsersRepository, Depends(get_repository(UsersRepository))],
    ) -> UsersService:
        return UsersService(users_repository, caller_id)


users_service_factory = UsersDependencyChecker()
UsersServiceDep = Annotated[UsersService, Depends(users_service_factory)]
