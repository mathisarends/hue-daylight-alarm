from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Scene:
    """A Hue scene: the ID is its identity, the name is display metadata."""

    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class Room:
    """A Hue room together with the scenes that can be activated in it."""

    id: UUID
    name: str
    scenes: tuple[Scene, ...]
