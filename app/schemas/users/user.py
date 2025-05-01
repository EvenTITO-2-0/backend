from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.schemas.users.user_role import UserRoleSchema
from app.schemas.users.utils import UID


class UserFullNameSchema(BaseModel):
    name: str = Field(min_length=2, max_length=100, examples=["Pepe"])
    lastname: str = Field(min_length=2, max_length=100, examples=["Argento"])


class UserEmailSchema(BaseModel):
    email: EmailStr = Field(examples=["pepe.argento@email.com"])


class PublicUserSchema(UserFullNameSchema, UserEmailSchema):
    pass


class UserModifySchema(UserFullNameSchema):
    model_config = ConfigDict(from_attributes=True)
    identification_number: str | None = Field(min_length=2, max_length=20, examples=["12345678"], default=None)
    phone: str | None = Field(min_length=8, max_length=13, examples=["5491165501111"], default=None)
    address: str | None = Field(min_length=2, max_length=100, examples=["Paseo Colon 850"], default=None)
    city: str | None = Field(min_length=2, max_length=100, examples=["Ciudad Autónoma de Buenos Aires"], default=None)
    country: str | None = Field(min_length=2, max_length=100, examples=["Argentina"], default=None)

    @model_validator(mode="after")
    def validate_digits(self) -> Self:
        if self.identification_number and not self.identification_number.isdigit():
            raise ValueError("identification_number must be digits only")
        if self.phone and not self.phone.isdigit():
            raise ValueError("identification_number must be digits only")
        return self


class UserSchema(UserModifySchema, UserEmailSchema):
    pass


class UserReply(UserSchema, UserRoleSchema):
    id: UID
