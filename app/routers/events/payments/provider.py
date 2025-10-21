import json
import logging
from typing import Annotated
from urllib.parse import quote, unquote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response

from app.authorization.caller_id_dep import CallerIdDep
from app.authorization.organizer_dep import verify_is_organizer
from app.repository.events_repository import EventsRepository
from app.repository.provider_account_repository import ProviderAccountRepository
from app.repository.repository import get_repository
from app.schemas.payments.payment import PaymentStatusSchema
from app.schemas.provider.provider import ProviderAccountResponseSchema
from app.services.event_payments.event_payments_service_dep import EventPaymentsServiceWebhookDep
from app.services.provider.provider_service import ProviderService
from app.services.provider.provider_service_dep import ProviderServiceDep
from app.settings.settings import MercadoPagoSettings

settings = MercadoPagoSettings()
provider_router = APIRouter(prefix="/provider")
provider_global_router = APIRouter(prefix="/provider")
logger = logging.getLogger(__name__)


@provider_router.get("/status", response_model=ProviderAccountResponseSchema | None)
async def get_provider_status(
    event_id: Annotated[UUID, Path(...)], provider_service: ProviderServiceDep
) -> ProviderAccountResponseSchema | None:
    logger.info("Getting provider status")
    logger.info(f"Event ID: {event_id}")
    return await provider_service.get_account_status(event_id)


@provider_router.get("/oauth/url", response_model=str, dependencies=[Depends(verify_is_organizer)])
async def get_oauth_url(event_id: Annotated[UUID, Path(...)], caller_id: CallerIdDep) -> str:
    if not settings.CLIENT_ID:
        raise HTTPException(status_code=400, detail="OAuth CLIENT_ID no configurado")
    if not settings.API_BASE_URL:
        raise HTTPException(status_code=500, detail="MERCADOPAGO_API_BASE_URL no configurado en el backend")
    redirect_uri = f"{settings.API_BASE_URL}/provider/oauth/callback"
    encoded_redirect = quote(redirect_uri, safe="")
    base = "https://auth.mercadopago.com/authorization"
    state = f"{event_id}:{caller_id}"
    return f"{base}?client_id={settings.CLIENT_ID}&response_type=code&redirect_uri={encoded_redirect}&state={state}"


@provider_global_router.get("/oauth/callback", response_model=None)
async def oauth_callback_global(
    code: str = Query(...),
    state: str = Query(...),
    provider_account_repository: Annotated[
        ProviderAccountRepository, Depends(get_repository(ProviderAccountRepository))
    ] = None,
    events_repository: Annotated[EventsRepository, Depends(get_repository(EventsRepository))] = None,
) -> Response:
    try:
        decoded_state = unquote(state)
        parts = decoded_state.split(":", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="state inválido")
        event_part, user_part = parts[0], parts[1]
        event_uuid = UUID(event_part)

        service = ProviderService(provider_account_repository, events_repository, event_uuid)
        await service.oauth_link_account_from_code(code, event_part, user_part)

        frontend_ok = f"{settings.FRONTEND_URL}/manage/{event_part}/administration?linked=1"
        return Response(status_code=302, headers={"Location": frontend_ok})

    except Exception as e:
        logger.exception(f"OAuth callback error: {str(e)}")
        frontend_fail = f"{settings.FRONTEND_URL}/manage/{state.split(':',1)[0]}/administration?linked=0"
        return Response(status_code=302, headers={"Location": frontend_fail})


@provider_router.get("/return/{result}", response_model=None)
async def provider_return(
    result: str,
    event_id: Annotated[UUID, Path(...)],
    request: Request,
    payments_service: EventPaymentsServiceWebhookDep,
) -> Response:
    qs = request.query_params
    ext_ref = qs.get("external_reference")
    collection_status = (qs.get("collection_status") or qs.get("status") or "").lower()

    status_map = {
        "approved": "APPROVED",
        "rejected": "REJECTED",
        "in_process": "PENDING_APPROVAL",
        "pending": "PENDING_APPROVAL",
        "cancelled": "REJECTED",
        "success": "APPROVED",
        "failure": "REJECTED",
    }
    chosen = status_map.get(collection_status) or status_map.get(result.lower())

    if ext_ref and chosen:
        try:
            await payments_service.update_payment_status(UUID(ext_ref), PaymentStatusSchema(status=chosen))
        except Exception:
            logger.exception(
                "Error actualizando status desde return",
                extra={
                    "event_id": str(event_id),
                    "external_reference": ext_ref,
                    "chosen": chosen,
                },
            )

    target = f"{settings.FRONTEND_URL}/events/{event_id}/roles/attendee"
    return Response(status_code=302, headers={"Location": target})


@provider_router.post("/webhook", status_code=200)
async def handle_webhook(request: Request, payments_service: EventPaymentsServiceWebhookDep) -> Response:
    body = await request.body()

    try:
        payload = {}
        if body:
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}
        payload["_query"] = {"id": request.query_params.get("id"), "topic": request.query_params.get("topic")}
        await payments_service.handle_webhook(payload)
        return Response(status_code=200)
    except Exception:
        logger.exception("Webhook processing error", extra={"payload": payload})
        return Response(status_code=200)
