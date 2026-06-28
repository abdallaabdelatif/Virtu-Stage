from __future__ import annotations

from typing import BinaryIO

import boto3
from botocore.config import Config
from starlette.concurrency import run_in_threadpool

from app.config import (
    R2_ACCESS_KEY_ID,
    R2_ACCOUNT_ID,
    R2_BUCKET_NAME,
    R2_SECRET_ACCESS_KEY,
    R2_SIGNED_URL_EXPIRES_SECONDS,
)


class StorageConfigurationError(RuntimeError):
    pass


class R2FileStorage:
    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if not all(
            [R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME]
        ):
            raise StorageConfigurationError(
                "R2 storage is not configured on the server"
            )
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=(
                    f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
                ),
                aws_access_key_id=R2_ACCESS_KEY_ID,
                aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                region_name="auto",
                config=Config(signature_version="s3v4"),
            )
        return self._client

    async def upload(
        self, file_object: BinaryIO, object_key: str, content_type: str
    ) -> None:
        client = self._get_client()
        await run_in_threadpool(
            client.upload_fileobj,
            file_object,
            R2_BUCKET_NAME,
            object_key,
            ExtraArgs={"ContentType": content_type},
        )

    async def delete(self, object_key: str) -> None:
        client = self._get_client()
        await run_in_threadpool(
            client.delete_object, Bucket=R2_BUCKET_NAME, Key=object_key
        )

    async def create_download_url(self, object_key: str) -> str:
        client = self._get_client()
        return await run_in_threadpool(
            client.generate_presigned_url,
            "get_object",
            Params={"Bucket": R2_BUCKET_NAME, "Key": object_key},
            ExpiresIn=R2_SIGNED_URL_EXPIRES_SECONDS,
        )


file_storage = R2FileStorage()
