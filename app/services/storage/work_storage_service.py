from uuid import UUID

from app.schemas.storage.schemas import DownloadURLSchema, UploadURLSchema
from app.services.storage.storage_service import StorageService


class WorkStorageService(StorageService):
    def __init__(self, event_id: UUID, work_id: UUID):
        super().__init__()
        self.event_id = event_id
        self.work_id = work_id

    async def get_submission_upload_url(self, submission_id: UUID) -> UploadURLSchema:
        return await self.storage_client.generate_signed_upload_url(
            bucket_name=self.storage_settings.WORKS_BUCKET,
            blob_name=f"{self.event_id}/works/{self.work_id}/submissions/{submission_id}",
        )

    async def get_submission_read_url(self, submission_id: UUID) -> DownloadURLSchema:
        return await self.storage_client.generate_signed_read_url(
            bucket_name=self.storage_settings.WORKS_BUCKET,
            blob_name=f"{self.event_id}/works/{self.work_id}/submissions/{submission_id}",
        )

    async def get_review_upload_url(self, review_id: UUID) -> UploadURLSchema:
        return await self.storage_client.generate_signed_upload_url(
            bucket_name=self.storage_settings.WORKS_BUCKET,
            blob_name=f"{self.event_id}/works/{self.work_id}/reviews/{review_id}",
        )

    async def get_review_read_url(self, review_id: UUID) -> DownloadURLSchema:
        return await self.storage_client.generate_signed_read_url(
            bucket_name=self.storage_settings.WORKS_BUCKET,
            blob_name=f"{self.event_id}/works/{self.work_id}/reviews/{review_id}",
        )
