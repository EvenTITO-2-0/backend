import datetime
from enum import Enum
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class MandatoryDates(str, Enum):
    START_DATE = "START_DATE"
    END_DATE = "END_DATE"
    SUBMISSION_DEADLINE_DATE = "SUBMISSION_DEADLINE_DATE"


class DateSchema(BaseModel):
    name: str | None = Field(min_length=2, max_length=100, examples=[MandatoryDates.START_DATE], default=None)
    label: str = Field(min_length=2, max_length=100, examples=["Presentacion trabajos"])
    description: str = Field(min_length=2, max_length=100, examples=["Inicio fecha"])
    is_mandatory: bool
    date: datetime.date | None = Field(examples=["2023-07-12"], default=None)
    time: datetime.time | None = Field(examples=["15:30"], default=None)


class DatesCompleteSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    dates: list[DateSchema] = Field(
        default=[
            DateSchema(
                name=MandatoryDates.START_DATE,
                label="Fecha de Comienzo",
                description="Fecha de comienzo del evento.",
                is_mandatory=True,
                date="2024-10-01",
                time="09:00:00",
            ),
            DateSchema(
                name=MandatoryDates.END_DATE,
                label="Fecha de Finalización",
                description="Fecha de comienzo del evento.",
                is_mandatory=True,
                date="2024-10-01",
                time="09:00:00",
            ),
            DateSchema(
                name=MandatoryDates.SUBMISSION_DEADLINE_DATE,
                label="Fecha de envío de trabajos",
                description="Fecha límite de envío de trabajos.",
                is_mandatory=True,
                date="2024-10-01",
                time="09:00:00",
            ),
        ]
    )

    @model_validator(mode="after")
    def check_mandatory_dates(self) -> Self:
        mandatory_dates = [date for date in self.dates if date.is_mandatory]
        if len(mandatory_dates) != len(MandatoryDates):
            raise ValueError("There should be 3 mandatory dates")

        for date_type in list(MandatoryDates):
            if date_type not in [date.name for date in mandatory_dates]:
                raise ValueError("All 3 mandatory dates should be present")

        mandatory_dates_dict = {}
        for date in mandatory_dates:
            mandatory_dates_dict[date.name] = date
        start_date = mandatory_dates_dict[MandatoryDates.START_DATE].date
        start_time = mandatory_dates_dict[MandatoryDates.START_DATE].time
        end_date = mandatory_dates_dict[MandatoryDates.END_DATE].date
        end_time = mandatory_dates_dict[MandatoryDates.END_DATE].time
        if start_date is not None and end_date is not None:
            if (start_date > end_date) or (start_date == end_date and start_time > end_time):
                raise ValueError("End Date should be after Start Date.")
        return self
