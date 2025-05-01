from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.author_dep import IsAuthorDep, verify_is_author
from app.authorization.chair_dep import IsWorkChairDep
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.reviewer_dep import IsWorkReviewerDep
from app.authorization.util_dep import or_
from app.schemas.works.submission import SubmissionDownloadSchema, SubmissionResponseSchema, SubmissionUploadSchema
from app.services.event_submissions.event_submissions_service_dep import SubmissionsServiceDep

works_submissions_router = APIRouter(
    prefix="/{event_id}/works/{work_id}/submissions", tags=["Event: Works Submissions"]
)


@works_submissions_router.put(
    path="/submit", status_code=201, response_model=SubmissionUploadSchema, dependencies=[Depends(verify_is_author)]
)
async def submit(submission_service: SubmissionsServiceDep) -> SubmissionUploadSchema:
    return await submission_service.do_submit()


# Si sos chair del track asignado al trabajo del cual queres ver la submission no vas a poder a no ser que te auto
# como reviewer del trabajo
@works_submissions_router.get(
    path="/latest",
    status_code=200,
    response_model=SubmissionDownloadSchema,
    dependencies=[or_(IsOrganizerDep, IsAdminUsrDep, IsAuthorDep, IsWorkReviewerDep)],
)
async def get_download_latest_submission_file(submission_service: SubmissionsServiceDep) -> SubmissionDownloadSchema:
    return await submission_service.get_latest_submission()


@works_submissions_router.get(
    path="/{submission_id}",
    status_code=200,
    response_model=SubmissionDownloadSchema,
    dependencies=[or_(IsOrganizerDep, IsAdminUsrDep, IsAuthorDep, IsWorkReviewerDep)],
)
async def get_download_submission_file(
    submission_id: UUID, submission_service: SubmissionsServiceDep
) -> SubmissionDownloadSchema:
    return await submission_service.get_submission(submission_id)


@works_submissions_router.get(
    path="",
    status_code=200,
    response_model=list[SubmissionResponseSchema],
    dependencies=[or_(IsOrganizerDep, IsAuthorDep, IsWorkChairDep, IsWorkReviewerDep)],
)
async def get_all_submissions(
    submission_service: SubmissionsServiceDep, offset: int = 0, limit: int = Query(default=100, le=100)
) -> list[SubmissionResponseSchema]:
    return await submission_service.get_all_event_submissions(offset, limit)
