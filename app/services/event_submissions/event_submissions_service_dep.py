from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.authorization.caller_id_dep import CallerIdDep
from app.repository.repository import get_repository
from app.repository.submissions_repository import SubmissionsRepository
from app.services.event_submissions.event_submissions_service import SubmissionsService
from app.services.storage.work_storage_service_dep import WorkStorageServiceDep
from app.services.works.works_service_dep import WorksServiceDep


class Submissions:
    async def __call__(
        self,
        user_id: CallerIdDep,
        event_id: UUID,
        work_id: UUID,
        work_service: WorksServiceDep,
        storage_service: WorkStorageServiceDep,
        submission_repository: Annotated[SubmissionsRepository, Depends(get_repository(SubmissionsRepository))],
    ) -> SubmissionsService:
        return SubmissionsService(submission_repository, work_service, storage_service, user_id, event_id, work_id)


submissions_service = Submissions()
SubmissionsServiceDep = Annotated[SubmissionsService, Depends(submissions_service)]
