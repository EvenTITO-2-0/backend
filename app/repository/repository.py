from typing import Type, TypeVar

from app.database.session_dep import SessionDep
from app.repository.crud_repository import Repository

T = TypeVar("T", bound="Repository")


def get_repository(repository: Type[T], *args):
    async def _get_repository(session: SessionDep):
        return repository(session, *args)

    return _get_repository
