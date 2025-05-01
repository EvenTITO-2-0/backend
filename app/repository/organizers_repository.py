from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.organizer import OrganizerModel
from app.repository.members_repository import MemberRepository


class OrganizerRepository(MemberRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, OrganizerModel)

    def _primary_key_conditions(self, primary_key):
        event_id, organizer_id = primary_key
        return [OrganizerModel.event_id == event_id, OrganizerModel.user_id == organizer_id]
