from pydantic import BaseModel

from app.database.models.user import UserRole


class UserRoleSchema(BaseModel):
    role: UserRole
