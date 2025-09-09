from uuid import UUID

from app.exceptions.payments_exceptions import PaymentNotFound
from app.repository.payments_repository import PaymentsRepository
from app.schemas.payments.payment import PaymentRequestSchema, PaymentResponseSchema, PaymentStatusSchema
from app.schemas.users.utils import UID
from app.services.services import BaseService
from app.services.storage.event_inscription_storage_service import EventInscriptionStorageService
from app.database.models.payment import PaymentStatus
from mercadopago import SDK
from app.repository.provider_account_repository import ProviderAccountRepository
from app.repository.events_repository import EventsRepository
from app.settings.settings import MercadoPagoSettings
from fastapi import HTTPException


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
        self._settings = MercadoPagoSettings()

    async def pay_inscription(self, inscription_id: UUID, payment_request: PaymentRequestSchema) -> dict:
        payment_id = await self.payments_repository.do_new_payment(
            self.event_id,
            inscription_id,
            payment_request
        )

        event = await self.events_repository.get(self.event_id)
        access_token = None

        if event.provider_account_id:
            provider_account = await self.provider_account_repository.get(event.provider_account_id)
            access_token = provider_account.access_token
        else:
            if self._settings.ENABLE_ENV_PROVIDER_FALLBACK and self._settings.ACCESS_TOKEN:
                access_token = self._settings.ACCESS_TOKEN

        if not getattr(event, "pricing", None):
            raise HTTPException(status_code=400, detail="El evento no tiene tarifas configuradas")

        fare = next((f for f in event.pricing if f.get("name") == payment_request.fare_name), None)
        if fare is None:
            raise HTTPException(status_code=400, detail=f"Tarifa '{payment_request.fare_name}' no encontrada")

        try:
            raw_value = fare.get("value", 0)
            amount = float(raw_value) if not isinstance(raw_value, (int, float)) else float(raw_value)
        except Exception:
            raise HTTPException(status_code=400, detail="Valor de tarifa inválido")

        if amount <= 0:
            raise HTTPException(status_code=400, detail="El monto de la tarifa debe ser mayor a 0")

        frontend_base = self._settings.FRONTEND_URL.rstrip('/')
        api_base = self._settings.API_BASE_URL.rstrip('/')
        back_urls = {
            "success": f"{api_base}/events/{event.id}/provider/return/success",
            "failure": f"{api_base}/events/{event.id}/provider/return/failure",
            "pending": f"{api_base}/events/{event.id}/provider/return/pending",
        }
        notification_url = f"{api_base}/events/{event.id}/provider/webhook"

        if not access_token:
            upload_url = await self.storage_service.get_payment_upload_url(self.user_id, payment_id)
            return {
                "payment_id": payment_id,
                "upload_url": upload_url,
            }

        mp = SDK(access_token)

        preference_data = {
            "items": [
                {
                    "title": f"Pago para {event.title}",
                    "quantity": 1,
                    "currency_id": "ARS",
                    "unit_price": float(amount),
                }
            ],
            "external_reference": str(payment_id),
            "back_urls": back_urls,
            "auto_return": "approved",
            "notification_url": notification_url,
        }

        preference_response = mp.preference().create(preference_data)
        checkout_data = preference_response.get("response", {})
        init_point = checkout_data.get("init_point") or checkout_data.get("sandbox_init_point")

        if not init_point:
            raise HTTPException(status_code=502, detail={
                "message": "Mercado Pago no devolvió checkout_url",
                "mp_status": preference_response.get("status"),
                "mp_response": checkout_data,
            })

        return {
            "payment_id": payment_id,
            "checkout_url": init_point,
            "preference_id": checkout_data.get("id") or checkout_data.get("preference_id", "")
        }

    async def handle_webhook(self, payment_data: dict) -> None:
        payment_id = payment_data.get("external_reference")
        if not payment_id:
            raise ValueError("Missing external_reference in webhook data")

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

        await self.update_payment_status(UUID(payment_id), new_status)

    async def get_inscription_payment(self, inscription_id: UUID, payment_id: UUID) -> PaymentResponseSchema:
        return await self.payments_repository.get_payment(self.event_id, inscription_id, payment_id)

    async def get_event_payments(self, offset: int, limit: int) -> list[PaymentResponseSchema]:
        return await self.payments_repository.get_all_payments_for_event(self.event_id, offset, limit)

    async def get_inscription_payments(
        self, inscription_id: UUID, offset: int, limit: int
    ) -> list[PaymentResponseSchema]:
        return await self.payments_repository.get_payments_for_inscription(self.event_id, inscription_id, offset, limit)

    async def update_payment_status(self, payment_id: UUID, new_status: PaymentStatusSchema) -> None:
        update_ok = await self.payments_repository.update_status(self.event_id, payment_id, new_status)
        if not update_ok:
            raise PaymentNotFound(self.event_id, payment_id)
        return
