from typing import Annotated

from fastapi import Depends, HTTPException

from app.authorization.user_id_dep import UserDep
from app.database.models.user import UserRole


class IsAdminUser:
    async def __call__(self, role: UserDep) -> bool:
        return role == UserRole.ADMIN


IsAdminUsrDep = Annotated[bool, Depends(IsAdminUser())]


class VerifyIsAdminUser:
    async def __call__(self, is_admin: IsAdminUsrDep) -> None:
        if not is_admin:
            raise HTTPException(status_code=403)


verify_is_admin_user = VerifyIsAdminUser()
AdminUsrDep = Annotated[None, Depends(verify_is_admin_user)]
