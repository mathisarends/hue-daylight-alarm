from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class LightResource(StrEnum):
    ROOM = "room"
    SCENE = "scene"


@dataclass(frozen=True, slots=True)
class LightChange:
    """A room or scene changed on the bridge.

    The bridge reports only the fields that moved, so ``name`` is set when the
    resource was renamed and None for every other change -- including a
    deletion, which arrives as a bare identity.
    """

    resource: LightResource
    id: UUID
    name: str | None = None
