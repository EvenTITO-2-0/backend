from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageTypes(str, Enum):
    GCP_STORAGE = "GCP_STORAGE"
    NO_STORAGE = "NO_STORAGE"


class StorageSettings(BaseSettings):
    EVENTS_BUCKET: str
    WORKS_BUCKET: str
    CERTIFICATES_BUCKET: str
    USERS_BUCKET: str
    PUBLIC_BASE_URL: str
    TYPE_STORAGE: StorageTypes
    GCP_CREDENTIALS: str | None = None


class MercadoPagoSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MERCADOPAGO_")
    PUBLIC_KEY: str | None = None
    ACCESS_TOKEN: str | None = None
    WEBHOOK_SECRET: str | None = None
    FRONTEND_URL: str = "http://localhost:5173"
    API_BASE_URL: str = ""
    ENABLE_ENV_PROVIDER_FALLBACK: bool = False
    MARKETPLACE_NAME: str = "TPP-2"
    CLIENT_ID: str | None = None
    CLIENT_SECRET: str | None = None


# TODO: Validar que si ENABLE_SEND_EMAILS==True, entonces lo otro este setteado.
class NotificationsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NOTIFICATIONS_")
    EMAIL: str | None = None
    EMAIL_PASSWORD: str | None = None
    FRONTEND_URL: str = ""
    ENABLE_SEND_EMAILS: bool = False
    SMTPS_PORT: int = 465


class DatabaseSettings(BaseSettings):
    DATABASE_URL: str
