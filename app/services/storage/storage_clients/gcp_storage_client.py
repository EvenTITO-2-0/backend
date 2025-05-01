import json

from google.cloud import storage
from google.oauth2 import service_account

from app.schemas.storage.schemas import DownloadURLSchema, UploadURLSchema


class GCPStorageClient:
    def __init__(self, gcp_client):
        self.gcp_client = gcp_client

    async def generate_signed_upload_url(
        self, bucket_name, blob_name, expiration=3600, max_size_mb=3
    ) -> UploadURLSchema:
        blob = await self.__get_blob(bucket_name, blob_name)
        url = blob.generate_signed_url(version="v4", expiration=expiration, method="PUT")

        return UploadURLSchema(upload_url=url, expiration_time_seconds=expiration, max_upload_size_mb=max_size_mb)

    async def generate_signed_read_url(
        self,
        bucket_name,
        blob_name,
        expiration=3600,
    ) -> DownloadURLSchema:
        blob = await self.__get_blob(bucket_name, blob_name)

        url = blob.generate_signed_url(version="v4", expiration=expiration, method="GET")
        return DownloadURLSchema(
            download_url=url,
            expiration_time_seconds=expiration,
        )

    async def __get_blob(self, bucket_name, blob_name):
        if not self.gcp_client:
            raise Exception("No Storage Client provided.")
        bucket = self.gcp_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob


def get_gcp_storage_client(storage_settings):
    if storage_settings.GCP_CREDENTIALS is None:
        raise Exception("GCP_CREDENTIALS variable should be setted for TYPE_STORAGE=GCP_STORAGE.")
    service_account_info = json.loads(storage_settings.GCP_CREDENTIALS)
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    storage_client = storage.Client(credentials=credentials)
    return GCPStorageClient(storage_client)
