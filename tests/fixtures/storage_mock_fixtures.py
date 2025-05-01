from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.storage.schemas import DownloadURLSchema, UploadURLSchema


@pytest.fixture(scope="session", autouse=True)
def mock_storage():
    base_path = "app.services.storage.storage_clients"
    gcp_path = f"{base_path}.gcp_storage_client.GCPStorageClient"
    no_client_path = f"{base_path}.no_storage_provided_client.NoStorageProvidedClient"

    async def mock_generate_upload_url(*args, **kwargs):
        return UploadURLSchema(upload_url="mocked-url-upload", expiration_time_seconds=3600, max_upload_size_mb=5)

    async def mock_generate_download_url(*args, **kwargs):
        return DownloadURLSchema(download_url="mocked-url-download", expiration_time_seconds=3600)

    patches = [
        patch(f"{gcp_path}.generate_signed_upload_url", new_callable=AsyncMock, side_effect=mock_generate_upload_url),
        patch(f"{gcp_path}.generate_signed_read_url", new_callable=AsyncMock, side_effect=mock_generate_download_url),
        patch(
            f"{no_client_path}.generate_signed_upload_url", new_callable=AsyncMock, side_effect=mock_generate_upload_url
        ),
        patch(
            f"{no_client_path}.generate_signed_read_url", new_callable=AsyncMock, side_effect=mock_generate_download_url
        ),
    ]

    for p in patches:
        p.start()

    yield

    for p in patches:
        p.stop()
