from logging import getLogger
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from mercadopago import SDK

from app.database.models.inscription import InscriptionStatus
from app.database.models.payment import PaymentStatus
from app.exceptions.payments_exceptions import PaymentNotFound
from app.repository.events_repository import EventsRepository
from app.repository.inscriptions_repository import InscriptionsRepository
from app.repository.payments_repository import PaymentsRepository
from app.repository.provider_account_repository import ProviderAccountRepository
from app.schemas.inscriptions.inscription import InscriptionStatusSchema
from app.schemas.payments.payment import (
    PaymentRequestSchema,
    PaymentResponseSchema,
    PaymentStatusSchema,
)
from app.schemas.users.utils import UID
from app.services.services import BaseService
from app.services.storage.event_inscription_storage_service import EventInscriptionStorageService
from app.settings.settings import MercadoPagoSettings

logger = getLogger(__name__)


class EventPaymentsService(BaseService):
    def __init__(
        self,
        storage_service: EventInscriptionStorageService,
        payments_repository: PaymentsRepository,
        inscriptions_repository: InscriptionsRepository,
        provider_account_repository: ProviderAccountRepository,
        events_repository: EventsRepository,
        event_id: UUID,
        user_id: UID,
    ):
        self.storage_service = storage_service
        self.payments_repository = payments_repository
        self.inscriptions_repository = inscriptions_repository
        self.provider_account_repository = provider_account_repository
        self.events_repository = events_repository
        self.event_id = event_id
        self.user_id = user_id
        self._settings = MercadoPagoSettings()

    async def pay_inscription(self, inscription_id: UUID, payment_request: PaymentRequestSchema) -> dict:
        payment_id = await self.payments_repository.do_new_payment(self.event_id, inscription_id, payment_request)
        event = await self.events_repository.get(self.event_id)
        access_token = None
        if event.provider_account_id:
            provider_account = await self.provider_account_repository.get(event.provider_account_id)
            access_token = provider_account.access_token
        elif self._settings.ENABLE_ENV_PROVIDER_FALLBACK and self._settings.ACCESS_TOKEN:
            access_token = self._settings.ACCESS_TOKEN
        if not access_token:
            raise HTTPException(status_code=400, detail="El organizador no configuró Mercado Pago para este evento")
        if not getattr(event, "pricing", None):
            raise HTTPException(status_code=400, detail="El evento no tiene tarifas configuradas")
        fare = next((f for f in event.pricing if f.get("name") == payment_request.fare_name), None)
        if fare is None:
            raise HTTPException(status_code=400, detail=f"Tarifa '{payment_request.fare_name}' no encontrada")
        try:
            raw_value = fare.get("value", 0)
            amount = float(raw_value) if not isinstance(raw_value, (int, float)) else float(raw_value)
        except Exception as err:
            raise HTTPException(status_code=400, detail="Valor de tarifa inválido") from err
        if amount < 0:
            raise HTTPException(status_code=400, detail="El monto de la tarifa no puede ser negativo")
        if amount == 0:
            await self.payments_repository.update_provider_fields(
                payment_id,
                {
                    "amount": 0.0,
                    "currency": "ARS",
                },
            )
            await self.update_payment_status(payment_id, PaymentStatusSchema(status=PaymentStatus.APPROVED))
            return {
                "payment_id": payment_id,
                "free": True,
            }
        if not self._settings.API_BASE_URL:
            raise HTTPException(status_code=500, detail="MERCADOPAGO_API_BASE_URL no configurado en el backend")
        api_base = self._settings.API_BASE_URL.rstrip("/")
        back_urls = {
            "success": f"{api_base}/events/{event.id}/provider/return/success",
            "failure": f"{api_base}/events/{event.id}/provider/return/failure",
            "pending": f"{api_base}/events/{event.id}/provider/return/pending",
        }
        notification_url = f"{api_base}/events/{event.id}/provider/webhook"
        mp = SDK(access_token)
        now_utc = datetime.now(timezone.utc)
        expiration_from = now_utc.isoformat(timespec="seconds").replace("+00:00", "Z")
        expiration_to = (now_utc + timedelta(minutes=self._settings.CHECKOUT_EXPIRES_MINUTES)).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z")
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
            "expires": True,
            "expiration_date_from": expiration_from,
            "expiration_date_to": expiration_to,
            "binary_mode": bool(self._settings.BINARY_MODE),
        }
        preference_response = mp.preference().create(preference_data)
        checkout_data = preference_response.get("response", {})
        init_point = checkout_data.get("init_point") or checkout_data.get("sandbox_init_point")
        if not init_point:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Mercado Pago no devolvió checkout_url",
                    "mp_status": preference_response.get("status"),
                    "mp_response": checkout_data,
                },
            )
        await self.payments_repository.update_provider_fields(
            payment_id,
            {
                "amount": amount,
                "currency": "ARS",
                "provider_preference_id": checkout_data.get("id") or checkout_data.get("preference_id", ""),
            },
        )
        return {
            "payment_id": payment_id,
            "checkout_url": init_point,
            "preference_id": checkout_data.get("id") or checkout_data.get("preference_id", ""),
        }

    async def handle_webhook(self, payment_data: dict) -> None:  # noqa: C901
        query = payment_data.get("_query", {}) if isinstance(payment_data, dict) else {}
        q_id = query.get("id")
        q_topic = query.get("topic")

        logger.info(
            "Webhook recibido",
            extra={
                "event_id": str(self.event_id),
                "topic": q_topic,
                "query_id": q_id,
                "has_body": bool(payment_data),
            },
        )

        external_reference = payment_data.get("external_reference") if isinstance(payment_data, dict) else None
        status = payment_data.get("status") if isinstance(payment_data, dict) else None
        preference_id = payment_data.get("preference_id") if isinstance(payment_data, dict) else None
        provider_payment_id = None
        if isinstance(payment_data, dict):
            provider_payment_id = payment_data.get("id") or payment_data.get("data", {}).get("id")

        event = await self.events_repository.get(self.event_id)
        access_token = None
        if event.provider_account_id:
            provider_account = await self.provider_account_repository.get(event.provider_account_id)
            access_token = provider_account.access_token
        elif self._settings.ENABLE_ENV_PROVIDER_FALLBACK and self._settings.ACCESS_TOKEN:
            access_token = self._settings.ACCESS_TOKEN

        # merchant_order -> payment
        mo = None
        if access_token and q_topic == "merchant_order" and q_id and not (external_reference and status):
            mp = SDK(access_token)
            try:
                mo_resp = mp.merchant_order().get(q_id)
                mo = mo_resp.get("response", {})
                payments = mo.get("payments", []) or []
                logger.info(
                    "Merchant order obtenida",
                    extra={
                        "event_id": str(self.event_id),
                        "mo_id": q_id,
                        "payments_count": len(payments),
                    },
                )
                if payments:
                    provider_payment_id = str(payments[-1].get("id"))
                    pr_resp = mp.payment().get(provider_payment_id)
                    pr = pr_resp.get("response", {})
                    external_reference = external_reference or pr.get("external_reference")
                    status = status or pr.get("status")
                # fallback: merchant_order.external_reference
                external_reference = external_reference or mo.get("external_reference")
            except Exception:
                logger.exception(
                    "Error consultando merchant_order/payment",
                    extra={
                        "event_id": str(self.event_id),
                        "mo_id": q_id,
                        "provider_payment_id": provider_payment_id,
                    },
                )

        if not external_reference and preference_id:
            try:
                ref = await self.payments_repository.get_payment_id_by_preference_id(self.event_id, preference_id)
                if ref:
                    external_reference = str(ref)
                    logger.info(
                        "Resuelto payment por preference_id",
                        extra={
                            "event_id": str(self.event_id),
                            "preference_id": preference_id,
                            "external_reference": external_reference,
                        },
                    )
            except Exception:
                logger.exception(
                    "Error resolviendo por preference_id",
                    extra={
                        "event_id": str(self.event_id),
                        "preference_id": preference_id,
                    },
                )

        if (not status) and mo:
            try:
                total_amount = float(mo.get("total_amount") or 0)
                paid_amount = float(mo.get("paid_amount") or 0)
                mo_status = (mo.get("status") or "").lower()
                logger.info(
                    "Inferencia desde merchant_order",
                    extra={
                        "event_id": str(self.event_id),
                        "mo_id": q_id,
                        "mo_status": mo_status,
                        "total_amount": total_amount,
                        "paid_amount": paid_amount,
                    },
                )
                if total_amount > 0 and paid_amount >= total_amount:
                    status = "approved"
                elif (
                    mo_status in ["opened", "payment_required", "partially_paid", "in_process"]
                    and paid_amount < total_amount
                ):
                    status = "pending"
                elif mo_status in ["cancelled", "closed"] and paid_amount == 0:
                    status = "rejected"
            except Exception:
                logger.exception(
                    "Error infiriendo estado desde merchant_order",
                    extra={
                        "event_id": str(self.event_id),
                        "mo_id": q_id,
                    },
                )

        if (not external_reference or not status) and provider_payment_id and access_token:
            mp = SDK(access_token)
            try:
                res = mp.payment().get(provider_payment_id)
                body = res.get("response", {})
                external_reference = external_reference or body.get("external_reference")
                status = status or body.get("status")
                if external_reference:
                    await self.payments_repository.update_provider_fields(
                        UUID(external_reference), {"provider_payment_id": str(provider_payment_id)}
                    )
                logger.info(
                    "Payment consultado",
                    extra={
                        "event_id": str(self.event_id),
                        "provider_payment_id": provider_payment_id,
                        "status": status,
                        "external_reference": external_reference,
                    },
                )
            except Exception:
                logger.exception(
                    "Error consultando payment",
                    extra={
                        "event_id": str(self.event_id),
                        "provider_payment_id": provider_payment_id,
                    },
                )

        if not external_reference or not status:
            logger.warning(
                "Webhook no resolvió pago",
                extra={
                    "event_id": str(self.event_id),
                    "topic": q_topic,
                    "query_id": q_id,
                    "provider_payment_id": provider_payment_id,
                    "external_reference": external_reference,
                    "status": status,
                },
            )
            return

        status_map = {
            "approved": PaymentStatus.APPROVED,
            "rejected": PaymentStatus.REJECTED,
            "pending": PaymentStatus.PENDING_APPROVAL,
            "in_process": PaymentStatus.PENDING_APPROVAL,
            "cancelled": PaymentStatus.REJECTED,
        }
        new_status = PaymentStatusSchema(status=status_map.get(status, PaymentStatus.UNCOMPLETED))
        await self.update_payment_status(UUID(external_reference), new_status)
        logger.info(
            "Pago actualizado",
            extra={
                "event_id": str(self.event_id),
                "payment_id": external_reference,
                "new_status": new_status.status,
            },
        )

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

        if new_status.status == PaymentStatus.APPROVED:
            # Traer el pago para conocer tarifa e inscripción
            payment_row = await self.payments_repository.get_payment_row(self.event_id, payment_id)
            if not payment_row:
                raise PaymentNotFound(self.event_id, payment_id)

            fare_name = getattr(payment_row, "fare_name", None)
            inscription_id = getattr(payment_row, "inscription_id", None)

            # Determinar si la tarifa requiere verificación manual
            need_verification = False
            try:
                event = await self.events_repository.get(self.event_id)
                pricing = getattr(event, "pricing", None) or []
                if fare_name:
                    for f in pricing:
                        if (f or {}).get("name") == fare_name:
                            need_verification = bool((f or {}).get("need_verification"))
                            break
            except Exception:
                # Si algo falla al obtener pricing, ser conservador: no autoaprobar
                need_verification = True

            # Solo autoaprobar inscripción si la tarifa NO requiere verificación
            if inscription_id and not need_verification:
                await self.inscriptions_repository.update_status(
                    self.event_id,
                    inscription_id,
                    InscriptionStatusSchema(status=InscriptionStatus.APPROVED),
                )
        return
