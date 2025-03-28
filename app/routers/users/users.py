from fastapi import APIRouter, Depends

from app.authorization.admin_user_dep import IsAdminUsrDep, verify_is_admin_user
from app.authorization.caller_id_dep import verify_user_id
from app.authorization.same_user_dep import IsSameUsrDep
from app.authorization.util_dep import or_
from app.routers.users.echo import echo_router
from app.routers.users.roles import user_roles_router
from app.schemas.users.user import UserModifySchema, UserReply, UserSchema
from app.schemas.users.utils import UID
from app.services.users.users_admin_service_dep import UsersAdminServiceDep
from app.services.users.users_service_dep import UsersServiceDep

users_router = APIRouter(
    prefix="/users",
)

users_router.include_router(echo_router)
users_router.include_router(user_roles_router)


@users_router.get(
    path="/{user_id}",
    response_model=UserReply,
    tags=["Users: General"],
    dependencies=[or_(IsSameUsrDep, IsAdminUsrDep)],
)
async def read_user(user_id: UID, users_service: UsersServiceDep):
    return await users_service.get(user_id)


@users_router.post(
    path="", status_code=201, response_model=str, tags=["Users: General"], dependencies=[Depends(verify_user_id)]
)
async def create_user(user: UserSchema, users_service: UsersServiceDep):
    return await users_service.create(user)


@users_router.put(
    path="/{user_id}",
    status_code=204,
    response_model=None,
    tags=["Users: General"],
    dependencies=[or_(IsSameUsrDep, IsAdminUsrDep)],
)
async def update_user(user: UserModifySchema, users_service: UsersServiceDep):
    await users_service.update(user)


@users_router.get(
    path="",
    response_model=list[UserReply],
    tags=["Users: Administration"],
    dependencies=[Depends(verify_is_admin_user)],
)
async def read_all_users(users_admin_service: UsersAdminServiceDep, limit: int = 100, offset: int = 0):
    return await users_admin_service.get_many(offset, limit)
