from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from starlette.concurrency import run_in_threadpool

from app.config import (
    R2_ACCESS_KEY_ID,
    R2_ACCOUNT_ID,
    R2_BUCKET_NAME,
    R2_AVATAR_BUCKET_NAME,
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

    async def delete_many(self, object_keys: list[str]) -> None:
        """Delete a presentation and all of its slides in one R2 request."""
        unique_keys = list(dict.fromkeys(object_keys))
        if not unique_keys:
            return
        client = self._get_client()
        response = await run_in_threadpool(
            client.delete_objects,
            Bucket=R2_BUCKET_NAME,
            Delete={
                "Objects": [{"Key": object_key} for object_key in unique_keys],
                "Quiet": True,
            },
        )
        errors = response.get("Errors", [])
        if errors:
            first = errors[0]
            raise ClientError(
                {
                    "Error": {
                        "Code": first.get("Code", "DeleteObjectsError"),
                        "Message": first.get("Message", "R2 object deletion failed"),
                    }
                },
                "DeleteObjects",
            )

    async def upload_path(
        self, local_path: Path, object_key: str, content_type: str
    ) -> None:
        client = self._get_client()
        await run_in_threadpool(
            client.upload_file,
            str(local_path),
            R2_BUCKET_NAME,
            object_key,
            ExtraArgs={"ContentType": content_type},
        )

    async def download_to_path(self, object_key: str, local_path: Path) -> None:
        client = self._get_client()
        await run_in_threadpool(
            client.download_file,
            R2_BUCKET_NAME,
            object_key,
            str(local_path),
        )

    async def create_download_url(self, object_key: str) -> str:
        client = self._get_client()
        return await run_in_threadpool(
            client.generate_presigned_url,
            "get_object",
            Params={"Bucket": R2_BUCKET_NAME, "Key": object_key},
            ExpiresIn=R2_SIGNED_URL_EXPIRES_SECONDS,
        )

    async def upload_avatar(self, file_object: BinaryIO, object_key: str) -> None:
        client = self._get_client()
        await run_in_threadpool(
            client.upload_fileobj,
            file_object,
            R2_AVATAR_BUCKET_NAME,
            object_key,
            ExtraArgs={"ContentType": "image/webp"},
        )

    async def read_avatar(self, object_key: str) -> bytes:
        client = self._get_client()

        def read_object() -> bytes:
            response = client.get_object(
                Bucket=R2_AVATAR_BUCKET_NAME,
                Key=object_key,
            )
            body = response["Body"]
            try:
                return body.read()
            finally:
                body.close()

        return await run_in_threadpool(read_object)

    async def delete_avatar(self, object_key: str) -> None:
        client = self._get_client()
        await run_in_threadpool(
            client.delete_object,
            Bucket=R2_AVATAR_BUCKET_NAME,
            Key=object_key,
        )


file_storage = R2FileStorage()
