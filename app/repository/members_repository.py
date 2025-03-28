from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import UserModel
from app.repository.crud_repository import Repository
from app.schemas.users.utils import UID


class MemberRepository(Repository):
    def __init__(self, session: AsyncSession, model):
        super().__init__(session, model)

    async def get_all(self, event_id: UUID):
        query = select(UserModel, self.model).where(
            and_(self.model.event_id == event_id, self.model.user_id == UserModel.id)
        )
        result = await self.session.execute(query)
        return result.fetchall()

    async def is_member(self, event_id: UUID, user_id: UID):
        conditions = [self.model.event_id == event_id, self.model.user_id == user_id]
        return await self._exists_with_conditions(conditions)

    async def get_member(self, event_id: UUID, user_id: UID):
        query = select(UserModel, self.model).where(
            and_(self.model.event_id == event_id, self.model.user_id == UserModel.id, UserModel.id == user_id)
        )
        result = await self.session.execute(query)
        return result.fetchone()

    async def remove_member(self, event_id, user_id):
        return await self.remove((event_id, user_id))

    async def create_member(self, event_id: UUID, user_id: UID):
        db_in = self.model(user_id=user_id, event_id=event_id)
        await self._create(db_in)
