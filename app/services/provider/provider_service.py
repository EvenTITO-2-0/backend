from logging import getLogger
from uuid import UUID
from typing import Annotated

import requests
from fastapi import Path

from app.services.services import BaseService
from app.repository.provider_account_repository import ProviderAccountRepository
from app.repository.events_repository import EventsRepository
from app.schemas.provider.provider import ProviderAccountSchema, ProviderAccountResponseSchema
from app.exceptions.provider_exceptions import (
    ProviderAccountNotFound,
    ProviderAccountAlreadyExists,
    InvalidProviderCredentials,
)

logger = getLogger(__name__)

class ProviderService(BaseService):
    def __init__(
        self,
        provider_account_repository: ProviderAccountRepository,
        events_repository: EventsRepository,
        event_id: Annotated[UUID, Path(...)]
    ):
        self.provider_account_repository = provider_account_repository
        self.events_repository = events_repository
        self.event_id = event_id

    async def link_account(self, event_id: UUID, account_data: ProviderAccountSchema) -> ProviderAccountResponseSchema:
        logger.info("Linking provider account", extra={"event_id": str(event_id), "account_data": account_data.model_dump()})
        event = await self.events_repository.get(event_id)
        if event.provider_account_id:
            raise ProviderAccountAlreadyExists(event_id)

        # Validar tokens con Mercado Pago API
        try:
            headers = {
                "Authorization": f"Bearer {account_data.access_token}"
            }
            response = requests.get("https://api.mercadopago.com/users/me", headers=headers)

            if response.status_code != 200:
                raise InvalidProviderCredentials("No se pudo validar el token de acceso")

            account_info = response.json()

            # Verificar que el account_id coincida
            if str(account_info.get("id")) != str(account_data.account_id):
                raise InvalidProviderCredentials("El ID de cuenta no coincide con el token proporcionado")

        except Exception as e:
            raise InvalidProviderCredentials(f"Error al validar credenciales: {str(e)}")

        data = account_data.model_dump()
        data["user_id"] = event.creator_id
        account = await self.provider_account_repository.create(data)
        await self.events_repository.update(
                    event_id,
                    {"provider_account_id": account.id}
                )

        return ProviderAccountResponseSchema.from_orm(account)

    async def get_account_status(self, event_id: UUID) -> ProviderAccountResponseSchema | None:
        logger.info("Getting account status for event", extra={"event_id": str(event_id)})
        account = await self.provider_account_repository.get_by_event_id(event_id)
        if not account:
            return None
        return ProviderAccountResponseSchema(**account.__dict__)
