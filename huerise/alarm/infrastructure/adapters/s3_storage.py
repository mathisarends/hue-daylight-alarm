from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import aioboto3
from botocore.config import Config

from huerise.alarm.application.storage import (
    StorageBackend,
    StorageFile,
    UploadResponse,
)
from huerise.alarm.infrastructure.credentials import StorageSettings

_S3_CLIENT_CONFIG = Config(
    signature_version="s3v4",
    s3={"addressing_style": "path"},
)


class S3StorageBackend(StorageBackend):
    """S3-compatible storage adapter for alarm sounds."""

    def __init__(self, settings: StorageSettings) -> None:
        self._session = aioboto3.Session()
        self._settings = settings

    @asynccontextmanager
    async def _client(self) -> AsyncGenerator[Any]:
        async with self._session.client(
            service_name="s3",
            endpoint_url=self._settings.endpoint_url,
            region_name="us-east-1",
            aws_access_key_id=self._settings.access_key,
            aws_secret_access_key=self._settings.secret_key,
            config=_S3_CLIENT_CONFIG,
        ) as client:
            yield client

    async def download_bytes(self, path: str) -> bytes:
        async with self._client() as s3:
            response = await s3.get_object(
                Bucket=self._settings.bucket_name,
                Key=path,
            )
            async with response["Body"] as body:
                return await body.read()

    async def upload_bytes(
        self,
        path: str,
        data: bytes,
        content_type: str | None = None,
    ) -> UploadResponse:
        request: dict[str, Any] = {
            "Bucket": self._settings.bucket_name,
            "Key": path,
            "Body": data,
        }
        if content_type is not None:
            request["ContentType"] = content_type

        async with self._client() as s3:
            await s3.put_object(**request)

        return UploadResponse(storage_path=path)

    async def list_files(self, path: str = "") -> list[StorageFile]:
        files: list[StorageFile] = []
        continuation_token: str | None = None

        async with self._client() as s3:
            while True:
                request: dict[str, Any] = {
                    "Bucket": self._settings.bucket_name,
                    "Prefix": path,
                }
                if continuation_token is not None:
                    request["ContinuationToken"] = continuation_token

                response = await s3.list_objects_v2(**request)
                files.extend(
                    StorageFile(
                        name=obj["Key"].rsplit("/", maxsplit=1)[-1],
                        storage_path=obj["Key"],
                    )
                    for obj in response.get("Contents", [])
                    if not obj["Key"].endswith("/")
                )

                if not response.get("IsTruncated", False):
                    break
                continuation_token = response["NextContinuationToken"]

        return files
