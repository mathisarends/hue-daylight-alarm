from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StorageFile:
    name: str
    storage_path: str


@dataclass(frozen=True, slots=True)
class UploadResponse:
    storage_path: str


class StorageBackend(ABC):
    """Port for generic object storage access."""

    @abstractmethod
    async def upload_bytes(
        self,
        path: str,
        data: bytes,
        content_type: str | None = None,
    ) -> UploadResponse: ...

    @abstractmethod
    async def download_bytes(self, path: str) -> bytes: ...

    @abstractmethod
    async def list_files(self, path: str = "") -> list[StorageFile]: ...
