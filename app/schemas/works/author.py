from pydantic import BaseModel, Field


class AuthorInformation(BaseModel):
    full_name: str = Field(examples=["Juan Sanchez"])
    membership: str | None = Field(examples=["FIUBA"], default=None)
    mail: str = Field(examples=["juansanchez@mail.com"])
    notify_updates: bool = Field(
        description=(
            "If set to true, the author will receive emails "
            "with the work updates (reviews, deadline date notification)"
        ),
        default=False,
    )
    is_speaker: bool = Field(description="If set to true, the author is speaker", default=False)
    is_main: bool = Field(description="If set to true, the author is who submitted the work", default=False)
