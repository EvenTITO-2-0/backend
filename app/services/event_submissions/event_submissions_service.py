from uuid import UUID

from app.database.models.submission import SubmissionModel
from app.database.models.work import WorkStates
from app.exceptions.submissions.submissions_exceptions import SubmissionNotFound
from app.repository.submissions_repository import SubmissionsRepository
from app.schemas.users.utils import UID
from app.schemas.works.submission import SubmissionDownloadSchema, SubmissionResponseSchema, SubmissionUploadSchema
from app.services.services import BaseService
from app.services.storage.work_storage_service import WorkStorageService
from app.services.works.works_service import WorksService


class SubmissionsService(BaseService):
    def __init__(
        self,
        submission_repository: SubmissionsRepository,
        work_service: WorksService,
        storage_service: WorkStorageService,
        user_id: UID,
        event_id: UUID,
        work_id: UUID,
    ):
        self.submission_repository = submission_repository
        self.work_service = work_service
        self.storage_service = storage_service
        self.user_id = user_id
        self.event_id = event_id
        self.work_id = work_id

    async def get_all_event_submissions(self, offset: int, limit: int) -> list[SubmissionResponseSchema]:
        submissions = await self.submission_repository.get_all_submissions_for_event(
            self.event_id, self.work_id, offset, limit
        )
        return list(map(SubmissionsService.__map_to_schema, submissions))

    async def do_submit(self) -> SubmissionUploadSchema:
        await self.work_service.validate_update_work(self.work_id)
        my_work = await self.work_service.get_work(self.work_id)
        if my_work.state == WorkStates.RE_SUBMIT:
            submission_id = await self.submission_repository.do_new_submit(self.event_id, self.work_id)
        else:
            last_submission = await self.submission_repository.get_last_submission(self.event_id, self.work_id)
            if last_submission is None:
                submission_id = await self.submission_repository.do_new_submit(self.event_id, self.work_id)
            else:
                submission_id = await self.submission_repository.update_submit(last_submission.id)
        upload_url = await self.storage_service.get_submission_upload_url(submission_id)
        return SubmissionUploadSchema(
            id=submission_id,
            event_id=self.event_id,
            work_id=self.work_id,
            state=WorkStates.SUBMITTED,
            upload_url=upload_url,
        )

    async def get_submission(self, submission_id: UUID) -> SubmissionDownloadSchema:
        submission = await self.submission_repository.get(submission_id)
        return await self.__get_submission(submission)

    async def get_latest_submission(self) -> SubmissionDownloadSchema:
        last_submission = await self.submission_repository.get_last_submission(self.event_id, self.work_id)
        return await self.__get_submission(last_submission)

    async def __get_submission(self, submission: SubmissionModel) -> SubmissionDownloadSchema:
        if submission is None:
            raise SubmissionNotFound(self.event_id, self.work_id)
        download_url = await self.storage_service.get_submission_read_url(submission.id)
        return SubmissionDownloadSchema(
            id=submission.id,
            event_id=submission.event_id,
            work_id=submission.work_id,
            state=submission.state,
            download_url=download_url,
            creation_date=submission.creation_date,
            last_update=submission.last_update,
        )

    @staticmethod
    def __map_to_schema(model: SubmissionModel) -> SubmissionResponseSchema:
        return SubmissionResponseSchema(
            id=model.id,
            work_id=model.work_id,
            event_id=model.event_id,
            state=model.state,
            creation_date=model.creation_date,
            last_update=model.last_update,
        )
