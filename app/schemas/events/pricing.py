from pydantic import (
    BaseModel,
    Field,
)

from app.schemas.events.dates import MandatoryDates
from app.schemas.events.roles import EventRole


class FareSchema(BaseModel):
    name: str = Field(examples=["Students Only Fee"])
    description: str = Field(examples=["Only Students with certificate"])
    value: int = Field(examples=[50])
    currency: str = Field(examples=["ARS"], default="ARS")
    roles: list[EventRole] = Field(default_factory=list)
    related_date: str | None = Field(examples=[MandatoryDates.START_DATE], default=None)
    need_verification: bool = Field(description="If its True, a validation file must be added in the inscription form")


class PricingSchema(BaseModel):
    pricing: list[FareSchema] = Field(default_factory=list)
