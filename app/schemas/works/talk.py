from datetime import datetime

from pydantic import BaseModel, Field


class Talk(BaseModel):
    date: datetime | None = Field(examples=["2024-01-01T09:00:00"], default=None)
    location: str | None = Field(max_length=200, examples=["FIUBA, Av. Paseo Colon 850"], default="")
    duration: int | None = Field(examples=[60], default=None)
