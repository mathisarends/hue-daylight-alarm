from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class LightResource(StrEnum):
    ROOM = "room"
    SCENE = "scene"


@dataclass(frozen=True, slots=True)
class LightChange:
    """The bridge sends only the fields that moved, so ``name`` is set on a
    rename and None otherwise -- a deletion arrives as a bare identity."""

    resource: LightResource
    id: UUID
    name: str | None = None
