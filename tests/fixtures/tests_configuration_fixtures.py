import pytest
from httpx import ASGITransport, AsyncClient

from app.database.database import SessionLocal, engine
from app.database.models.base import Base
from app.database.session_dep import get_db

# With this import, the Base metadate is filled with the Database Models.
from app.main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def setup_database(anyio_backend):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    yield


@pytest.fixture(scope="session")
async def connection(anyio_backend):
    async with engine.connect() as connection:
        yield connection


@pytest.fixture()
async def transaction(connection):
    async with connection.begin() as transaction:
        yield transaction


@pytest.fixture(scope="function")
async def session_override(connection, transaction):
    async def get_db_session_override():
        async_session = SessionLocal(
            bind=connection,
            join_transaction_mode="create_savepoint",
        )
        async with async_session:
            yield async_session

    app.dependency_overrides[get_db] = get_db_session_override
    yield
    del app.dependency_overrides[get_db]

    await transaction.rollback()


@pytest.fixture(scope="function")
async def client(session_override):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
