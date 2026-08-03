from dataclasses import dataclass
from enum import StrEnum
from uuid import NAMESPACE_URL, UUID, uuid5

_ID_SEPARATOR = "/"
_ID_NAMESPACE = "huerise:sound:"


class SoundCategory(StrEnum):
    WAKE_UP = "wake_up"
    GET_UP = "get_up"

    @property
    def folder(self) -> str:
        """Storage prefix the files of this category live under."""
        return f"{self.value}_sounds"

    @property
    def file_prefix(self) -> str:
        """Filename prefix carried by every file of this category."""
        return f"{self.value.replace('_', '-')}-"


@dataclass(frozen=True, slots=True)
class Sound:
    """A playable audio file, addressed by a stable deterministic UUID.

    The id is what an alarm profile stores, so it must survive a re-upload:
    it is derived from category and file name, never from the object key.
    """

    id: UUID
    name: str
    category: SoundCategory
    storage_path: str

    @classmethod
    def from_storage_path(cls, storage_path: str) -> Sound | None:
        """None when the path is not a sound of a known category."""
        folder, separator, file_name = storage_path.partition(_ID_SEPARATOR)
        if not separator:
            return None

        category = next(
            (c for c in SoundCategory if c.folder == folder),
            None,
        )
        if category is None:
            return None

        name = file_name.rsplit(".", maxsplit=1)[0].removeprefix(category.file_prefix)
        if not name:
            return None

        return cls(
            id=uuid5(
                NAMESPACE_URL,
                f"{_ID_NAMESPACE}{category.value}{_ID_SEPARATOR}{name}",
            ),
            name=name,
            category=category,
            storage_path=storage_path,
        )
