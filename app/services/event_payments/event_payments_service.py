from uuid import UUID

from app.exceptions.payments_exceptions import PaymentNotFound
from app.repository.payments_repository import PaymentsRepository
from app.schemas.payments.payment import PaymentRequestSchema, PaymentsResponseSchema, PaymentStatusSchema
from app.schemas.users.utils import UID
from app.services.services import BaseService
from app.services.storage.event_inscription_storage_service import EventInscriptionStorageService
from app.database.models.payment import PaymentStatus
from mercadopago import SDK
from app.repository.provider_account_repository import ProviderAccountRepository
from app.repository.events_repository import EventsRepository


class EventPaymentsService(BaseService):
    def __init__(
        self,
        storage_service: EventInscriptionStorageService,
        payments_repository: PaymentsRepository,
        provider_account_repository: ProviderAccountRepository,
        events_repository: EventsRepository,
        event_id: UUID,
        user_id: UID,
    ):
        self.storage_service = storage_service
        self.payments_repository = payments_repository
        self.provider_account_repository = provider_account_repository
        self.events_repository = events_repository
        self.event_id = event_id
        self.user_id = user_id

    async def pay_inscription(self, inscription_id: UUID, payment_request: PaymentRequestSchema) -> dict:
        payment_id = await self.payments_repository.do_new_payment(
            self.event_id, 
            inscription_id, 
            payment_request
        )

        # Obtener el evento y su cuenta de proveedor
        event = await self.events_repository.get(self.event_id)
        if not event.provider_account_id:
            raise Exception(f"Provider account not linked for event {self.event_id}")

        provider_account = await self.provider_account_repository.get(event.provider_account_id)

        # Inicializar SDK de Mercado Pago con las credenciales del proveedor
        mp = SDK(provider_account.access_token)

        # Calcular la comisión del marketplace
        amount = payment_request.amount
        if provider_account.marketplace_fee_type == "percentage":
            marketplace_fee = amount * (provider_account.marketplace_fee / 100)
        else:
            marketplace_fee = provider_account.marketplace_fee

        # Crear preferencia de pago
        preference_data = {
            "items": [
                {
                    "title": f"Pago para {event.title}",
                    "quantity": 1,
                    "currency_id": "ARS",
                    "unit_price": float(amount),
                }
            ],
            "marketplace": "TPP-2",
            "marketplace_fee": float(marketplace_fee),
            "external_reference": str(payment_id),
            "back_urls": {
                "success": f"/events/{event.id}/payments/success",
                "failure": f"/events/{event.id}/payments/failure",
                "pending": f"/events/{event.id}/payments/pending"
            },
            "auto_return": "approved",
            "notification_url": f"/api/events/{event.id}/payments/webhook"
        }

        preference_response = mp.preference().create(preference_data)
        checkout_data = preference_response["response"]

        return {
            "payment_id": payment_id,
            "checkout_url": checkout_data["init_point"],
            "preference_id": checkout_data["id"]
        }

    async def handle_webhook(self, payment_data: dict) -> None:
        # Extraer información relevante del webhook
        payment_id = payment_data.get("external_reference")
        if not payment_id:
            raise ValueError("Missing external_reference in webhook data")

        # Mapear el estado de Mercado Pago a nuestro estado interno
        mp_status = payment_data.get("status")
        if not mp_status:
            raise ValueError("Missing status in webhook data")

        status_map = {
            "approved": PaymentStatus.APPROVED,
            "rejected": PaymentStatus.REJECTED,
            "pending": PaymentStatus.PENDING_APPROVAL,
            "in_process": PaymentStatus.PENDING_APPROVAL,
            "cancelled": PaymentStatus.REJECTED
        }
        
        new_status = PaymentStatusSchema(status=status_map.get(mp_status, PaymentStatus.UNCOMPLETED))
        
        # Actualizar el estado del pago
        await self.update_payment_status(UUID(payment_id), new_status)

    async def get_inscription_payment(self, inscription_id: UUID, payment_id: UUID) -> PaymentsResponseSchema:
        return await self.payments_repository.get_payment(self.event_id, inscription_id, payment_id)

    async def get_event_payments(self, offset: int, limit: int) -> list[PaymentsResponseSchema]:
        return await self.payments_repository.get_all_payments_for_event(self.event_id, offset, limit)

    async def get_inscription_payments(
        self, inscription_id: UUID, offset: int, limit: int
    ) -> list[PaymentsResponseSchema]:
        return await self.payments_repository.get_payments_for_inscription(self.event_id, inscription_id, offset, limit)

    async def update_payment_status(self, payment_id: UUID, new_status: PaymentStatusSchema) -> None:
        update_ok = await self.payments_repository.update_status(self.event_id, payment_id, new_status)
        if not update_ok:
            raise PaymentNotFound(self.event_id, payment_id)
        return
