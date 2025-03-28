import pytest

from app.database.database import SessionLocal, engine
from app.database.models.user import UserRole
from app.repository.events_repository import EventsRepository
from app.repository.users_repository import UsersRepository
from app.schemas.users.user import UserReply


@pytest.fixture(scope="session")
async def get_UsersRepository():
    session = SessionLocal(
        bind=engine,
    )
    users_repo = UsersRepository(session)
    return users_repo


@pytest.fixture(scope="session")
async def get_EventsRepository():
    session = SessionLocal(
        bind=engine,
    )
    events_repo = EventsRepository(session)
    return events_repo


@pytest.fixture(scope="session")
async def admin_data():
    session = SessionLocal(
        bind=engine,
    )

    user_id = "iuaealdasldanfas982983297232"
    user_to_create = UserReply(
        name="Jorge", lastname="Benitez", email="jbenitez@email.com", id=user_id, role=UserRole.ADMIN
    )
    users_repo = UsersRepository(session)
    await users_repo.create(user_to_create)
    user = await users_repo.get(user_id)
    await session.close()
    return user
