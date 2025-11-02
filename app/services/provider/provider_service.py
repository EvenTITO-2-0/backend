from logging import getLogger
from typing import Annotated
from uuid import UUID

import requests  # type: ignore[import-untyped]
from fastapi import Path

from app.exceptions.provider_exceptions import (
    InvalidProviderCredentials,
    ProviderAccountAlreadyExists,
)
from app.repository.events_repository import EventsRepository
from app.repository.provider_account_repository import ProviderAccountRepository
from app.schemas.provider.provider import ProviderAccountResponseSchema, ProviderAccountSchema
from app.services.services import BaseService
from app.settings.settings import MercadoPagoSettings

logger = getLogger(__name__)
settings = MercadoPagoSettings()


class ProviderService(BaseService):
    def __init__(
        self,
        provider_account_repository: ProviderAccountRepository,
        events_repository: EventsRepository,
        event_id: Annotated[UUID, Path(...)],
    ):
        self.provider_account_repository = provider_account_repository
        self.events_repository = events_repository
        self.event_id = event_id

    async def link_account(self, event_id: UUID, account_data: ProviderAccountSchema) -> ProviderAccountResponseSchema:
        logger.info(
            "Linking provider account", extra={"event_id": str(event_id), "account_data": account_data.model_dump()}
        )
        event = await self.events_repository.get(event_id)
        if event.provider_account_id:
            raise ProviderAccountAlreadyExists(event_id)

        try:
            headers = {"Authorization": f"Bearer {account_data.access_token}"}
            response = requests.get("https://api.mercadopago.com/users/me", headers=headers)

            if response.status_code != 200:
                raise InvalidProviderCredentials("No se pudo validar el token de acceso")

            account_info = response.json()

            if str(account_info.get("id")) != str(account_data.account_id):
                raise InvalidProviderCredentials("El ID de cuenta no coincide con el token proporcionado")

        except Exception as e:
            raise InvalidProviderCredentials(f"Error al validar credenciales: {str(e)}") from e

        existing = await self.provider_account_repository.get_by_provider_and_account_id(
            "mercadopago", account_data.account_id
        )
        if existing:
            for k in ["access_token", "refresh_token", "public_key"]:
                setattr(existing, k, getattr(account_data, k))
            existing.account_status = "ACTIVE"
            self.provider_account_repository.session.add(existing)
            await self.provider_account_repository.session.commit()
            account = existing
        else:
            data = account_data.model_dump()
            data["user_id"] = event.creator_id
            data["account_status"] = "ACTIVE"
            account = await self.provider_account_repository.create_from_dict(data)

        await self.events_repository.update(event_id, {"provider_account_id": account.id})

        return ProviderAccountResponseSchema.from_orm(account)

    async def get_account_status(self, event_id: UUID) -> ProviderAccountResponseSchema | None:
        logger.info("Getting account status for event", extra={"event_id": str(event_id)})
        account = await self.provider_account_repository.get_by_event_id(event_id)
        if not account:
            try:
                event = await self.events_repository.get(event_id)
                pricing = getattr(event, "pricing", None) or []
                event_is_free = (
                    isinstance(pricing, list) and len(pricing) == 1 and ((pricing[0] or {}).get("value") == 0)
                )
                if event_is_free:
                    free_provider = {
                        "id": "00000000-0000-0000-0000-000000000000",
                        "user_id": "free",
                        "provider": "free",
                        "access_token": "",
                        "refresh_token": "",
                        "public_key": "",
                        "account_id": "free",
                        "marketplace_fee": 0.0,
                        "marketplace_fee_type": "percentage",
                        "account_status": "ACTIVE",
                    }
                    return ProviderAccountResponseSchema(**free_provider)
            except Exception:
                logger.exception(
                    "Error evaluando proveedor free por evento gratuito", extra={"event_id": str(event_id)}
                )
            if settings.ENABLE_ENV_PROVIDER_FALLBACK and settings.ACCESS_TOKEN and settings.PUBLIC_KEY:
                fallback = {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "user_id": "env",
                    "provider": "mercadopago",
                    "access_token": settings.ACCESS_TOKEN,
                    "refresh_token": "",
                    "public_key": settings.PUBLIC_KEY,
                    "account_id": "env",
                    "marketplace_fee": 0.0,
                    "marketplace_fee_type": "percentage",
                    "account_status": "ACTIVE",
                }
                return ProviderAccountResponseSchema(**fallback)
            return None
        return ProviderAccountResponseSchema(**account.__dict__)

    async def oauth_link_account_from_code(self, code: str, state_event_id: str, state_user_id: str):
        """Intercambia el code de OAuth por tokens y vincula la cuenta al evento indicado en state con el usuario autenticado."""
        if not settings.CLIENT_ID or not settings.CLIENT_SECRET:
            logger.error("CLIENT_ID/CLIENT_SECRET not configured")
            raise InvalidProviderCredentials("OAuth CLIENT_ID/CLIENT_SECRET not configured")

        logger.info("Requesting token from Mercado Pago")
        token_url = "https://api.mercadopago.com/oauth/token"
        redirect_uri = f"{settings.API_BASE_URL}/provider/oauth/callback"
        form = {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        token_res = requests.post(token_url, data=form, headers=headers)
        logger.info(f"Token response status: {token_res.status_code}")

        if token_res.status_code != 200:
            logger.error(f"Token request failed: {token_res.text}")
            raise InvalidProviderCredentials(f"Could not exchange code: {token_res.status_code} {token_res.text}")

        token_data = token_res.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token", "")
        logger.info(f"Token received: {access_token[:20] if access_token else 'None'}...")

        logger.info("Getting user info from Mercado Pago")
        headers_me = {"Authorization": f"Bearer {access_token}"}
        me_res = requests.get("https://api.mercadopago.com/users/me", headers=headers_me)
        logger.info(f"User info response status: {me_res.status_code}")

        if me_res.status_code != 200:
            logger.error(f"User info request failed: {me_res.text}")
            raise InvalidProviderCredentials("Could not get user info")

        me = me_res.json()
        account_id = str(me.get("id"))
        public_key = settings.PUBLIC_KEY or ""
        logger.info(f"Account ID: {account_id}")

        logger.info("Processing event and account")
        event_uuid = UUID(state_event_id)
        logger.info(f"Event retrieved: {event_uuid}")

        logger.info("Checking for existing provider account")
        existing = await self.provider_account_repository.get_by_provider_and_account_id("mercadopago", account_id)
        logger.info(f"Existing account found: {existing is not None}")

        if existing:
            logger.info("Updating existing account")
            update_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "public_key": public_key,
                "account_status": "ACTIVE",
            }
            for k, v in update_data.items():
                setattr(existing, k, v)
            self.provider_account_repository.session.add(existing)
            await self.provider_account_repository.session.commit()
            account = existing
            logger.info(f"Account updated - ID: {account.id}")
        else:
            logger.info("Creating new account")
            data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "public_key": public_key,
                "account_id": account_id,
                "user_id": state_user_id,
                "provider": "mercadopago",
                "account_status": "ACTIVE",
                "marketplace_fee": 0.0,
                "marketplace_fee_type": "percentage",
            }
            account = await self.provider_account_repository.create_from_dict(data)
            logger.info(f"Account created - ID: {account.id}")

        logger.info("Updating event with provider_account_id")
        await self.events_repository.update(event_uuid, {"provider_account_id": account.id})
        logger.info(f"Event {event_uuid} updated with provider_account_id: {account.id}")

        updated_event = await self.events_repository.get(event_uuid)
        logger.info(f"Verification - Event provider_account_id: {updated_event.provider_account_id}")

        result = ProviderAccountResponseSchema.from_orm(account)
        logger.info("Response created successfully")

        return result
