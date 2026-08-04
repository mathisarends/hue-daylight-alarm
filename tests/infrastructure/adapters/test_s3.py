from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from huerise.infrastructure.storage.impl.s3 import S3StorageBackend
from huerise.infrastructure.storage.settings import StorageSettings

BUCKET = "huerise-assets"


def make_backend(
    s3_client: AsyncMock, *, public_endpoint_url: str | None = None
) -> tuple[S3StorageBackend, list[str | None]]:
    """A backend whose `_client` yields `s3_client` instead of a real aioboto3 one.

    Records the ``endpoint_url`` each call was made with, so a test can assert
    on which endpoint (private vs. public) a given operation used.
    """
    settings = StorageSettings(
        _env_file=None, bucket_name=BUCKET, public_endpoint_url=public_endpoint_url
    )
    backend = S3StorageBackend(settings)
    endpoints_used: list[str | None] = []

    @asynccontextmanager
    async def fake_client(endpoint_url: str | None = None) -> AsyncIterator[AsyncMock]:
        endpoints_used.append(endpoint_url)
        yield s3_client

    backend._client = fake_client
    return backend, endpoints_used


@pytest.fixture
def s3_client() -> AsyncMock:
    return AsyncMock()


async def test_downloads_the_object_body(s3_client: AsyncMock) -> None:
    body = MagicMock()
    body.__aenter__ = AsyncMock(return_value=body)
    body.__aexit__ = AsyncMock(return_value=False)
    body.read = AsyncMock(return_value=b"hello")
    s3_client.get_object.return_value = {"Body": body}
    backend, _ = make_backend(s3_client)

    data = await backend.download_bytes("sounds/a.mp3")

    assert data == b"hello"
    s3_client.get_object.assert_awaited_once_with(Bucket=BUCKET, Key="sounds/a.mp3")


async def test_uploads_bytes_without_a_content_type(s3_client: AsyncMock) -> None:
    backend, _ = make_backend(s3_client)

    response = await backend.upload_bytes("sounds/a.mp3", b"hi")

    assert response.storage_path == "sounds/a.mp3"
    s3_client.put_object.assert_awaited_once_with(
        Bucket=BUCKET, Key="sounds/a.mp3", Body=b"hi"
    )


async def test_uploads_bytes_with_a_content_type(s3_client: AsyncMock) -> None:
    backend, _ = make_backend(s3_client)

    await backend.upload_bytes("sounds/a.mp3", b"hi", content_type="audio/mpeg")

    s3_client.put_object.assert_awaited_once_with(
        Bucket=BUCKET, Key="sounds/a.mp3", Body=b"hi", ContentType="audio/mpeg"
    )


async def test_lists_files_and_skips_directory_markers(s3_client: AsyncMock) -> None:
    s3_client.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "sounds/"},
            {"Key": "sounds/a.mp3"},
            {"Key": "sounds/nested/b.mp3"},
        ],
        "IsTruncated": False,
    }
    backend, _ = make_backend(s3_client)

    files = await backend.list_files("sounds/")

    assert [(f.name, f.storage_path) for f in files] == [
        ("a.mp3", "sounds/a.mp3"),
        ("b.mp3", "sounds/nested/b.mp3"),
    ]
    s3_client.list_objects_v2.assert_awaited_once_with(Bucket=BUCKET, Prefix="sounds/")


async def test_lists_files_across_pages(s3_client: AsyncMock) -> None:
    s3_client.list_objects_v2.side_effect = [
        {
            "Contents": [{"Key": "a.mp3"}],
            "IsTruncated": True,
            "NextContinuationToken": "page-2",
        },
        {"Contents": [{"Key": "b.mp3"}], "IsTruncated": False},
    ]
    backend, _ = make_backend(s3_client)

    files = await backend.list_files()

    assert [f.storage_path for f in files] == ["a.mp3", "b.mp3"]
    first_call, second_call = s3_client.list_objects_v2.await_args_list
    assert "ContinuationToken" not in first_call.kwargs
    assert second_call.kwargs["ContinuationToken"] == "page-2"


async def test_lists_files_with_no_contents(s3_client: AsyncMock) -> None:
    s3_client.list_objects_v2.return_value = {"IsTruncated": False}
    backend, _ = make_backend(s3_client)

    assert await backend.list_files() == []


async def test_public_url_signs_a_get_request(s3_client: AsyncMock) -> None:
    s3_client.generate_presigned_url.return_value = "https://example.com/a.mp3?sig=x"
    backend, _ = make_backend(s3_client)

    url = await backend.public_url("sounds/a.mp3")

    assert url == "https://example.com/a.mp3?sig=x"
    s3_client.generate_presigned_url.assert_awaited_once_with(
        "get_object",
        Params={"Bucket": BUCKET, "Key": "sounds/a.mp3"},
        ExpiresIn=3600,
    )


async def test_public_url_prefers_the_public_endpoint(s3_client: AsyncMock) -> None:
    backend, endpoints_used = make_backend(
        s3_client, public_endpoint_url="http://192.168.1.5:9000"
    )

    await backend.public_url("sounds/a.mp3")

    assert endpoints_used == ["http://192.168.1.5:9000"]


async def test_download_and_upload_use_the_private_endpoint(
    s3_client: AsyncMock,
) -> None:
    backend, endpoints_used = make_backend(
        s3_client, public_endpoint_url="http://192.168.1.5:9000"
    )

    await backend.upload_bytes("a.mp3", b"hi")

    assert endpoints_used == [None]
