from typing import Type, TypeVar, Any

from app.database.session_dep import SessionDep
from app.repository.crud_repository import Repository

T = TypeVar("T", bound="Repository")


def get_repository(repository: Type[T]) -> Any:
    async def _get_repository(session: SessionDep) -> T:
        return repository(session)  # type: ignore
    return _get_repository
