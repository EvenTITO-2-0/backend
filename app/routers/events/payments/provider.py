import hashlib
import hmac
import json
from uuid import UUID
import logging
from typing import Annotated
from fastapi import APIRouter, Request, Response, HTTPException, Depends, Path, Query
from pydantic import BaseModel

from app.authorization.inscripted_dep import IsRegisteredDep
from app.authorization.organizer_dep import verify_is_organizer
from app.schemas.payments.payment import PaymentRequestSchema, PaymentResponseSchema
from app.schemas.provider.provider import ProviderAccountSchema, ProviderAccountResponseSchema
from app.services.event_payments.event_payments_service_dep import EventPaymentsServiceDep
from app.services.provider.provider_service_dep import ProviderServiceDep
from app.services.provider.provider_service import ProviderService
from app.repository.provider_account_repository import ProviderAccountRepository
from app.repository.events_repository import EventsRepository
from app.repository.repository import get_repository
from app.settings.settings import MercadoPagoSettings

settings = MercadoPagoSettings()
provider_router = APIRouter(prefix="/provider")
provider_global_router = APIRouter(prefix="/provider")
logger = logging.getLogger(__name__)


class PaymentCheckoutSchema(BaseModel):
    payment_id: UUID
    checkout_url: str | None = None
    preference_id: str | None = None
    upload_url: dict | None = None


@provider_router.post(
    "/link",
    response_model=None,
    dependencies=[]
)
async def link_provider_account(
    account_data: ProviderAccountSchema,
    event_id: Annotated[UUID, Path(...)],
    provider_service: ProviderServiceDep
) -> ProviderAccountResponseSchema:
    print(account_data)
    print(event_id)
    return await provider_service.link_account(event_id, account_data)

@provider_router.get(
    "/status",
    response_model=ProviderAccountResponseSchema | None
)
async def get_provider_status(
    event_id: Annotated[UUID, Path(...)],
    provider_service: ProviderServiceDep
) -> ProviderAccountResponseSchema | None:
    logger.info("Getting provider status")
    return await provider_service.get_account_status(event_id)

@provider_router.get(
    "/oauth/url",
    response_model=str,
    dependencies=[Depends(verify_is_organizer)]
)
async def get_oauth_url(event_id: Annotated[UUID, Path(...)]) -> str:
    if not settings.CLIENT_ID:
        raise HTTPException(status_code=400, detail="OAuth CLIENT_ID no configurado")
    redirect_uri = f"{settings.API_BASE_URL}/provider/oauth/callback"
    base = "https://auth.mercadopago.com/authorization"
    return f"{base}?client_id={settings.CLIENT_ID}&response_type=code&platform_id=mp&redirect_uri={redirect_uri}&state={event_id}"

@provider_global_router.get(
    "/oauth/callback",
    response_model=None
)
async def oauth_callback_global(
    code: str = Query(...),
    state: str = Query(...),
    provider_account_repository: Annotated[ProviderAccountRepository, Depends(get_repository(ProviderAccountRepository))] = None,
    events_repository: Annotated[EventsRepository, Depends(get_repository(EventsRepository))] = None,
) -> Response:
    try:
        service = ProviderService(provider_account_repository, events_repository, UUID(state))
        await service.oauth_link_account_from_code(code, state)
        frontend_ok = f"{settings.FRONTEND_URL}/manage/{state}/payments?linked=1"
        return Response(status_code=302, headers={"Location": frontend_ok})
    except Exception as e:
        logger.exception("OAuth callback error")
        frontend_fail = f"{settings.FRONTEND_URL}/manage/{state}/payments?linked=0"
        return Response(status_code=302, headers={"Location": frontend_fail})

@provider_router.post(
    "/checkout",
    response_model=PaymentCheckoutSchema,
    dependencies=[Depends(IsRegisteredDep)]
)
async def create_checkout(
    payment_request: PaymentRequestSchema,
    payments_service: EventPaymentsServiceDep
) -> PaymentCheckoutSchema:
    payment_data = await payments_service.pay_inscription(payment_request.inscription_id, payment_request)
    return payment_data

@provider_router.post(
    "/webhook",
    status_code=200
)
async def handle_webhook(
    request: Request,
    payments_service: EventPaymentsServiceDep
) -> Response:
    signature = request.headers.get("x-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    body = await request.body()

    if settings.WEBHOOK_SECRET:
        expected_signature = hmac.new(
            settings.WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payment_data = json.loads(body)
        await payments_service.handle_webhook(payment_data)
        return Response(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))