from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


class HueUnavailableError(Exception):
    pass


class SceneNotFoundError(Exception):
    def __init__(self, scene_id: UUID) -> None:
        super().__init__(f"Hue scene not found: {scene_id}")
        self.scene_id = scene_id


@dataclass(frozen=True, slots=True)
class HueCredentials:
    bridge_ip: str
    app_key: str


@dataclass(frozen=True, slots=True)
class Scene:
    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class Room:
    id: UUID
    name: str
    scenes: tuple[Scene, ...]


@dataclass(frozen=True, slots=True)
class AvailableScene:
    id: UUID
    name: str
    room_id: UUID
    room_name: str


class HueClient(Protocol):
    async def list_rooms(self) -> list[Room]: ...

    async def activate_scene(self, scene_id: UUID, *, brightness: float) -> None: ...

    async def set_brightness(self, room_id: UUID, brightness: float) -> None: ...

    async def close(self) -> None: ...


class HueClientFactory(Protocol):
    def create(self, credentials: HueCredentials) -> HueClient: ...


class HueCredentialsSource(Protocol):
    def get(self) -> HueCredentials: ...


def room_for_scene(rooms: list[Room], scene_id: UUID) -> Room:
    room = next(
        (item for item in rooms if any(scene.id == scene_id for scene in item.scenes)),
        None,
    )
    if room is None:
        raise SceneNotFoundError(scene_id)
    return room
