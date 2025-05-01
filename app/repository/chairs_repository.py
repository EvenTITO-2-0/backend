from uuid import UUID

from sqlalchemy import and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.chair import ChairModel
from app.repository.members_repository import MemberRepository
from app.schemas.users.utils import UID


class ChairRepository(MemberRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ChairModel)

    def _primary_key_conditions(self, primary_key):
        event_id, chair_id = primary_key
        return [ChairModel.event_id == event_id, ChairModel.user_id == chair_id]

    async def update_tracks(self, event_id: UUID, user_id: UID, tracks: list[str]):
        update_query = (
            update(ChairModel)
            .where(and_(ChairModel.event_id == event_id, ChairModel.user_id == user_id))
            .values(tracks=tracks)
        )
        await self.session.execute(update_query)
        await self.session.commit()
