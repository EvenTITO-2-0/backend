# backend/app/repository/provider_account_repository.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from app.database.models.provider_account import ProviderAccountModel
from app.repository.crud_repository import Repository
from pydantic import BaseModel

class ProviderAccountRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ProviderAccountModel)

    async def get_by_user_id(self, user_id: UUID):
        conditions = [ProviderAccountModel.user_id == user_id]
        return await self._get_with_conditions(conditions)

    async def get_by_event_id(self, event_id: UUID):
        conditions = [ProviderAccountModel.events.any(id=event_id)]
        return await self._get_with_conditions(conditions)

    async def get_by_provider_and_account_id(self, provider: str, account_id: str):
        conditions = [
            ProviderAccountModel.provider == provider,
            ProviderAccountModel.account_id == account_id,
        ]
        return await self._get_with_conditions(conditions)

    async def create_from_dict(self, data: dict):
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj