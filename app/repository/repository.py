from typing import Type

from app.database.session_dep import SessionDep
from app.repository.crud_repository import Repository


def get_repository(repository: Type[Repository]):
    async def _get_repository(session: SessionDep):
        return repository(session)

    return _get_repository
