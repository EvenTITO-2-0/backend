# backend/app/schemas/provider/provider.py
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.models.provider_account import ProviderAccountStatus


class ProviderAccountSchema(BaseModel):
    access_token: str = Field(..., description="Token de acceso de Mercado Pago")
    refresh_token: str = Field("", description="Token de refresco de Mercado Pago (opcional)")
    public_key: str = Field(..., description="Clave pública de Mercado Pago")
    account_id: str = Field(..., description="ID de la cuenta de Mercado Pago")
    marketplace_fee: float = Field(0.0, description="Comisión del marketplace")
    marketplace_fee_type: str = Field("percentage", description="Tipo de comisión (percentage o fixed)")


class ProviderAccountResponseSchema(ProviderAccountSchema):
    id: UUID
    user_id: str
    provider: str
    account_status: ProviderAccountStatus

    class Config:
        from_attributes = True
