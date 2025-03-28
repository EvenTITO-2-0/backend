from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException

from app.authorization.caller_id_dep import CallerIdDep
from app.services.event_reviewers.event_reviewers_service_dep import EventReviewerServiceDep


class IsReviewer:
    async def __call__(self, caller_id: CallerIdDep, reviewer_service: EventReviewerServiceDep) -> bool:
        return await reviewer_service.is_reviewer_in_event(caller_id)


IsReviewerDep = Annotated[bool, Depends(IsReviewer())]


class VerifyIsReviewer:
    async def __call__(self, is_event_reviewer: IsReviewerDep) -> None:
        if not is_event_reviewer:
            raise HTTPException(status_code=403)


verify_is_reviewer = VerifyIsReviewer()
ReviewerDep = Annotated[None, Depends(verify_is_reviewer)]


class IsWorkReviewer:
    async def __call__(
        self,
        caller_id: CallerIdDep,
        work_id: UUID,
        reviewer_service: EventReviewerServiceDep,
    ) -> bool:
        return await reviewer_service.is_reviewer_of_work_in_event(caller_id, work_id)


IsWorkReviewerDep = Annotated[bool, Depends(IsWorkReviewer())]


class VerifyIsWorkReviewer:
    async def __call__(self, is_event_work_reviewer: IsWorkReviewerDep) -> None:
        if not is_event_work_reviewer:
            raise HTTPException(status_code=403)


verify_is_work_reviewer = VerifyIsWorkReviewer()
WorkReviewerDep = Annotated[None, Depends(verify_is_work_reviewer)]
