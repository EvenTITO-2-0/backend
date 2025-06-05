from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.database.models.payment import PaymentStatus
from app.schemas.storage.schemas import DownloadURLSchema, UploadURLSchema


class PaymentIdSchema(BaseModel):
    id: UUID


class PaymentDatesResponseSchema(BaseModel):
    creation_date: datetime
    last_update: datetime


class PaymentRequestSchema(BaseModel):
    fare_name: str = Field(examples=["tarifa de speaker"])
    works: list[UUID] | None

class PaymentStatusSchema(BaseModel):
    status: PaymentStatus = Field(examples=[PaymentStatus.APPROVED])


class PaymentWorkSchema(BaseModel):
    id: UUID
    title: str = Field(examples=["Titulo"])
    track: str = Field(examples=["Track"])


class PaymentResponseSchema(PaymentIdSchema, PaymentDatesResponseSchema):
    event_id: UUID
    inscription_id: UUID
    status: PaymentStatus
    fare_name: str = Field(examples=["tarifa de speaker"])
    works: list[PaymentWorkSchema] | None


class PaymentDownloadSchema(PaymentResponseSchema):
    model_config = ConfigDict(from_attributes=True)
    download_url: DownloadURLSchema | None = Field(default=None)


class PaymentUploadSchema(PaymentIdSchema):
    model_config = ConfigDict(from_attributes=True)
    upload_url: UploadURLSchema | None = Field(default=None)
