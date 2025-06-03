from enum import Enum
from sqlalchemy import Column, String, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.database.models.base import Base, ModelTemplate
from app.database.models.user import UIDType

class ProviderAccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    REJECTED = "REJECTED"

class ProviderAccountModel(ModelTemplate, Base):
    __tablename__ = "provider_accounts"

    user_id = Column(UIDType, ForeignKey("users.id"), nullable=False, unique=True)
    provider = Column(String, nullable=False, default="mercadopago")  # Para futuros proveedores
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    public_key = Column(String, nullable=False)
    account_id = Column(String, nullable=False)
    account_status = Column(String, nullable=False, default=ProviderAccountStatus.PENDING)
    marketplace_fee = Column(Float, nullable=False, default=0.0)  # Comisión del marketplace
    marketplace_fee_type = Column(String, nullable=False, default="percentage")  # percentage o fixed

    user = relationship("UserModel", back_populates="provider_account")
    events = relationship("EventModel", back_populates="payment_provider")