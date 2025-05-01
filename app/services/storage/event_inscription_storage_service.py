from uuid import UUID

from app.schemas.storage.schemas import DownloadURLSchema, UploadURLSchema
from app.schemas.users.utils import UID
from app.services.storage.storage_service import StorageService


class EventInscriptionStorageService(StorageService):
    def __init__(self, event_id: UUID):
        super().__init__()
        self.event_id = event_id

    async def get_affiliation_upload_url(self, user_id: UID, inscription_id: UUID) -> UploadURLSchema:
        return await self.storage_client.generate_signed_upload_url(
            bucket_name=self.storage_settings.CERTIFICATES_BUCKET,
            blob_name=f"{self.event_id}/users/{user_id}/affiliations/{inscription_id}",
        )

    async def get_affiliation_read_url(self, user_id: UID, inscription_id: UUID) -> DownloadURLSchema:
        return await self.storage_client.generate_signed_read_url(
            bucket_name=self.storage_settings.CERTIFICATES_BUCKET,
            blob_name=f"{self.event_id}/users/{user_id}/affiliations/{inscription_id}",
        )

    async def get_payment_upload_url(self, user_id: UID, payment_id: UUID) -> UploadURLSchema:
        return await self.storage_client.generate_signed_upload_url(
            bucket_name=self.storage_settings.CERTIFICATES_BUCKET,
            blob_name=f"{self.event_id}/users/{user_id}/payments/{payment_id}",
        )

    async def get_payment_read_url(self, user_id: UID, payment_id: UUID) -> DownloadURLSchema:
        return await self.storage_client.generate_signed_read_url(
            bucket_name=self.storage_settings.CERTIFICATES_BUCKET,
            blob_name=f"{self.event_id}/users/{user_id}/payments/{payment_id}",
        )
