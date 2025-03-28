from typing import List
from uuid import UUID

from fastapi import APIRouter

from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.util_dep import or_
from app.schemas.members.member_schema import MemberRequestSchema, MemberResponseWithRolesSchema, RolesRequestSchema
from app.schemas.users.utils import UID
from app.services.event_members.event_members_service_dep import EventMembersServiceDep

event_members_router = APIRouter(prefix="/{event_id}/members", tags=["Events: Members"])


@event_members_router.get(
    path="",
    status_code=200,
    response_model=List[MemberResponseWithRolesSchema],
    dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)],
)
async def read_event_members(members_service: EventMembersServiceDep) -> list[MemberResponseWithRolesSchema]:
    return await members_service.get_all_members()


@event_members_router.post(path="", status_code=201, dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)])
async def add_member(
    members_service: EventMembersServiceDep,
    member: MemberRequestSchema,
) -> UID:
    return await members_service.add_member(member)


@event_members_router.delete(
    path="/{user_id}", status_code=201, response_model=None, dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def remove_member(user_id: UID, member_service: EventMembersServiceDep) -> None:
    await member_service.remove_member(user_id)


@event_members_router.put(
    path="/{user_id}/roles", status_code=204, response_model=None, dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def update(
    roles: RolesRequestSchema, event_id: UUID, user_id: UID, member_service: EventMembersServiceDep
) -> None:
    await member_service.update_rol_member(user_id, roles)
