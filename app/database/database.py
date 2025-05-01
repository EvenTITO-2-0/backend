from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.settings.settings import DatabaseSettings

settings = DatabaseSettings()
engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, autocommit=False)
