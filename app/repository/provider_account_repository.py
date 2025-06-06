# backend/app/repository/provider_account_repository.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.provider_account import ProviderAccountModel
from app.repository.crud_repository import Repository

class ProviderAccountRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ProviderAccountModel)

    async def get_by_user_id(self, user_id: UUID):
        conditions = [ProviderAccountModel.user_id == user_id]
        return await self._get_with_conditions(conditions)

    async def get_by_event_id(self, event_id: UUID):
        conditions = [ProviderAccountModel.events.any(id=event_id)]
        return await self._get_with_conditions(conditions)

    async def create(self, data: dict):
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj