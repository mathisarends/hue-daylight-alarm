from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any

import aioboto3
from botocore.config import Config

from huerise.infrastructure.storage.port import (
    DEFAULT_LINK_LIFETIME,
    StorageBackend,
    StorageFile,
    UploadResponse,
)
from huerise.infrastructure.storage.settings import StorageSettings

_S3_CLIENT_CONFIG = Config(
    signature_version="s3v4",
    s3={"addressing_style": "path"},
)


class S3StorageBackend(StorageBackend):
    """S3-compatible object storage adapter."""

    def __init__(self, settings: StorageSettings) -> None:
        self._session = aioboto3.Session()
        self._settings = settings

    @asynccontextmanager
    async def _client(self, endpoint_url: str | None = None) -> AsyncGenerator[Any]:
        async with self._session.client(
            service_name="s3",
            endpoint_url=endpoint_url or self._settings.endpoint_url,
            region_name="us-east-1",
            aws_access_key_id=self._settings.access_key.get_secret_value(),
            aws_secret_access_key=self._settings.secret_key.get_secret_value(),
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

    async def public_url(
        self,
        path: str,
        lifetime: timedelta = DEFAULT_LINK_LIFETIME,
    ) -> str:
        async with self._client(self._settings.public_endpoint_url) as s3:
            return await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._settings.bucket_name, "Key": path},
                ExpiresIn=int(lifetime.total_seconds()),
            )
