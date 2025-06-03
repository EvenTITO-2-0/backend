from fastapi import APIRouter, Request, Response, HTTPException
from uuid import UUID
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.inscripted_dep import IsRegisteredDep
from app.schemas.provider.provider import ProviderAccountSchema, ProviderAccountResponseSchema
from app.schemas.payments.payment import PaymentRequestSchema, PaymentResponseSchema
from app.services.provider.provider_service_dep import ProviderServiceDep
from app.services.event_payments.event_payments_service_dep import EventPaymentsServiceDep
from app.settings.settings import settings
import hmac
import hashlib
import json

provider_router = APIRouter(prefix="/provider")

@provider_router.post(
    "/link",
    response_model=ProviderAccountResponseSchema,
    dependencies=[IsOrganizerDep]
)
async def link_provider_account(
    account_data: ProviderAccountSchema,
    event_id: UUID,
    provider_service: ProviderServiceDep
) -> ProviderAccountResponseSchema:
    return await provider_service.link_account(event_id, account_data)

@provider_router.get(
    "/status",
    response_model=ProviderAccountResponseSchema,
    dependencies=[IsOrganizerDep]
)
async def get_provider_status(
    event_id: UUID,
    provider_service: ProviderServiceDep
) -> ProviderAccountResponseSchema:
    return await provider_service.get_account_status(event_id)

@provider_router.post(
    "/checkout",
    response_model=PaymentResponseSchema,
    dependencies=[IsRegisteredDep]
)
async def create_checkout(
    payment_request: PaymentRequestSchema,
    event_id: UUID,
    payments_service: EventPaymentsServiceDep
) -> PaymentResponseSchema:
    return await payments_service.pay_inscription(payment_request.inscription_id, payment_request)

@provider_router.post(
    "/webhook",
    status_code=200
)
async def handle_webhook(
    request: Request,
    event_id: UUID,
    payments_service: EventPaymentsServiceDep
) -> Response:
    # Verificar la firma del webhook
    signature = request.headers.get("x-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    # Obtener el cuerpo del webhook
    body = await request.body()
    
    # Verificar la firma usando el secreto de Mercado Pago
    if settings.MERCADOPAGO.WEBHOOK_SECRET:
        expected_signature = hmac.new(
            settings.MERCADOPAGO.WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=400, detail="Invalid signature")

    # Procesar el webhook
    try:
        payment_data = json.loads(body)
        await payments_service.handle_webhook(payment_data)
        return Response(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))