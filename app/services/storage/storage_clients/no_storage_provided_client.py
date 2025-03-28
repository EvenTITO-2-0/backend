class NoStorageProvidedClient:
    async def generate_signed_upload_url(self, bucket_name, blob_name, expiration=3600, max_size_mb=3):
        raise Exception("No storage Client provided")

    async def generate_signed_read_url(
        self,
        bucket_name,
        blob_name,
        expiration=3600,
    ):
        raise Exception("No storage Client provided")
