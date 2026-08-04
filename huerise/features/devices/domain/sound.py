from datetime import datetime
from enum import StrEnum
from uuid import UUID

from huerise.shared.ddd import Entity


class SoundCategory(StrEnum):
    WAKE_UP = "wake_up"
    GET_UP = "get_up"


class Sound(Entity):
    """A playable audio file whose metadata is independent of object storage."""

    def __init__(
        self,
        name: str,
        category: SoundCategory,
        storage_path: str,
        id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(id, created_at)
        self.name = name
        self.category = category
        self.storage_path = storage_path
