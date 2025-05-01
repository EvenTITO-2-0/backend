from fastapi import APIRouter, Depends

from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.user_id_dep import verify_user_exists
from app.authorization.util_dep import or_
from app.schemas.events.review_skeleton.review_skeleton import ReviewSkeletonRequestSchema, ReviewSkeletonResponseSchema
from app.services.events.events_configuration_service_dep import EventsConfigurationServiceDep

review_skeleton_configuration_router = APIRouter(prefix="/review-skeleton")


@review_skeleton_configuration_router.put(
    path="", status_code=204, response_model=None, dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def change_review_skeleton(
    review_skeleton: ReviewSkeletonRequestSchema,
    events_configuration_service: EventsConfigurationServiceDep,
):
    await events_configuration_service.update_review_skeleton(review_skeleton)


@review_skeleton_configuration_router.get(
    path="", status_code=200, response_model=ReviewSkeletonResponseSchema, dependencies=[Depends(verify_user_exists)]
)
async def get_review_skeleton(
    events_configuration_service: EventsConfigurationServiceDep,
) -> ReviewSkeletonResponseSchema:
    return await events_configuration_service.get_review_skeleton()
