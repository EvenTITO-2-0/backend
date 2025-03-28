from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.inscription import InscriptionModel
from app.repository.crud_repository import Repository
from app.schemas.inscriptions.inscription import InscriptionRequestSchema, InscriptionStatusSchema
from app.schemas.users.utils import UID


class InscriptionsRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, InscriptionModel)

    async def inscription_exists(self, event_id: UUID, user_id: UID) -> bool:
        conditions = [InscriptionModel.event_id == event_id, InscriptionModel.user_id == user_id]
        return await self._exists_with_conditions(conditions)

    async def inscribe(self, event_id: UUID, user_id: UID, inscription: InscriptionRequestSchema) -> InscriptionModel:
        db_inscription = InscriptionModel(
            event_id=event_id, user_id=user_id, roles=inscription.roles, affiliation=inscription.affiliation
        )
        return await self._create(db_inscription)

    async def get_event_inscriptions(self, event_id: UUID, offset: int, limit: int) -> list[InscriptionModel]:
        conditions = [InscriptionModel.event_id == event_id]
        return await self._get_many_with_conditions(conditions, offset, limit)

    async def get_user_inscriptions(self, user_id: UID, offset: int, limit: int) -> list[InscriptionModel]:
        conditions = [InscriptionModel.user_id == user_id]
        return await self._get_many_with_conditions(conditions, offset, limit)

    async def get_event_user_inscription(self, event_id: UUID, user_id: UID) -> InscriptionModel:
        conditions = [InscriptionModel.user_id == user_id, InscriptionModel.event_id == event_id]
        return await self._get_with_conditions(conditions)

    async def get_user_inscription_by_id(self, user_id: UID, event_id: UUID, inscription_id: UUID) -> InscriptionModel:
        conditions = [
            InscriptionModel.id == inscription_id,
            InscriptionModel.user_id == user_id,
            InscriptionModel.event_id == event_id,
        ]
        return await self._get_with_conditions(conditions)

    async def update_inscription(
        self, inscription_update: InscriptionRequestSchema, event_id: UUID, inscription_id: UUID
    ) -> bool:
        conditions = [InscriptionModel.event_id == event_id, InscriptionModel.id == inscription_id]
        return await self._update_with_conditions(conditions, inscription_update)

    async def update_status(self, event_id: UUID, inscription_id: UUID, status: InscriptionStatusSchema) -> bool:
        conditions = [InscriptionModel.event_id == event_id, InscriptionModel.id == inscription_id]
        return await self._update_with_conditions(conditions, status)
