# backend/app/services/provider/provider_service.py
from logging import getLogger
from uuid import UUID
from app.services.services import BaseService
from app.repository.provider_account_repository import ProviderAccountRepository
from app.repository.events_repository import EventsRepository
from app.schemas.provider.provider import ProviderAccountSchema, ProviderAccountResponseSchema
from app.exceptions.provider_exceptions import ProviderAccountNotFound, ProviderAccountAlreadyExists, InvalidProviderCredentials
from mercadopago import SDK

logger = getLogger(__name__)

class ProviderService(BaseService):
    def __init__(
        self,
        provider_account_repository: ProviderAccountRepository,
        events_repository: EventsRepository,
        event_id: UUID
    ):
        self.provider_account_repository = provider_account_repository
        self.events_repository = events_repository
        self.event_id = event_id

    async def link_account(self, event_id: UUID, account_data: ProviderAccountSchema) -> ProviderAccountResponseSchema:
        event = await self.events_repository.get(event_id)
        if event.provider_account_id:
            raise ProviderAccountAlreadyExists(event_id)

        # Validar tokens con Mercado Pago API
        try:
            mp = SDK(account_data.access_token)
            # Intentar obtener información de la cuenta
            account_info = mp.users().get()
            if not account_info or account_info.get("status") != 200:
                raise InvalidProviderCredentials("No se pudo validar el token de acceso")
            
            # Verificar que el account_id coincida
            if str(account_info.get("response", {}).get("id")) != str(account_data.account_id):
                raise InvalidProviderCredentials("El ID de cuenta no coincide con el token proporcionado")
            
        except Exception as e:
            raise InvalidProviderCredentials(f"Error al validar credenciales: {str(e)}")
        
        account = await self.provider_account_repository.create(
            user_id=event.creator_id,
            **account_data.model_dump()
        )
        
        # Actualizar evento con la cuenta del proveedor
        await self.events_repository.update(
            event_id,
            {"provider_account_id": account.id}
        )
        
        return ProviderAccountResponseSchema(**account.__dict__)

    async def get_account_status(self, event_id: UUID) -> ProviderAccountResponseSchema:
        logger.info("Getting account status for event", extra={"event_id": str(event_id)})
        account = await self.provider_account_repository.get_by_event_id(event_id)
        if not account:
            raise ProviderAccountNotFound(event_id)
        return ProviderAccountResponseSchema(**account.__dict__)