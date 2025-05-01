from typing import Annotated

from fastapi import Depends, Header

from app.schemas.users.utils import UID


async def verify_user_id(X_User_Id: Annotated[UID, Header()]) -> str:
    return X_User_Id


CallerIdDep = Annotated[str, Depends(verify_user_id)]
