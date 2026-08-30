from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from hueify import Hueify

from huerise.configuration import HueEnvironment, YamlConfiguration


class HueUnavailableError(Exception):
    pass


class SceneNotFoundError(Exception):
    def __init__(self, scene_id: UUID, room_id: UUID | None = None) -> None:
        detail = f" in room {room_id}" if room_id is not None else ""
        super().__init__(f"Hue scene not found{detail}: {scene_id}")
        self.scene_id = scene_id


class RoomNotFoundError(Exception):
    def __init__(self, room_id: UUID) -> None:
        super().__init__(f"Hue room not found: {room_id}")
        self.room_id = room_id


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


class HueClient(Protocol):
    async def list_rooms(self) -> list[Room]: ...

    async def activate_scene(self, scene_id: UUID, *, brightness: float) -> None: ...

    async def set_brightness(self, room_id: UUID, brightness: float) -> None: ...

    async def close(self) -> None: ...


class HueClientFactory(Protocol):
    def create(self, credentials: HueCredentials) -> HueClient: ...


class HueCredentialsProvider:
    def __init__(
        self, configuration: YamlConfiguration, environment: HueEnvironment
    ) -> None:
        self._configuration = configuration
        self._environment = environment

    def get(self) -> HueCredentials:
        if self._environment.configured:
            assert self._environment.bridge_ip is not None
            assert self._environment.app_key is not None
            return HueCredentials(
                bridge_ip=str(self._environment.bridge_ip),
                app_key=self._environment.app_key.get_secret_value(),
            )

        hue = self._configuration.load_hue()
        if hue is None or hue.app_key is None:
            raise HueUnavailableError("Philips Hue Bridge is not configured")
        return HueCredentials(bridge_ip=str(hue.bridge_ip), app_key=hue.app_key)


class HueifyClientFactory:
    def create(self, credentials: HueCredentials) -> HueClient:
        return HueifyClient(Hueify(credentials.bridge_ip, credentials.app_key))


class HueifyClient:
    def __init__(self, client: Hueify) -> None:
        self._client = client

    async def list_rooms(self) -> list[Room]:
        rooms = (await self._client.rooms.list()).data
        return [
            Room(
                id=room.id,
                name=room.name,
                scenes=tuple(
                    Scene(id=scene.id, name=scene.name)
                    for scene in await self._client.rooms.scenes(room.id)
                ),
            )
            for room in rooms
        ]

    async def activate_scene(self, scene_id: UUID, *, brightness: float) -> None:
        await self._client.scenes.activate(scene_id, brightness=brightness)

    async def set_brightness(self, room_id: UUID, brightness: float) -> None:
        await self._client.rooms.set_brightness(room_id, brightness)

    async def close(self) -> None:
        await self._client.close()


def room_for_scene(
    rooms: list[Room], scene_id: UUID, *, room_id: UUID | None = None
) -> Room:
    if room_id is not None:
        room = next((room for room in rooms if room.id == room_id), None)
        if room is None:
            raise RoomNotFoundError(room_id)
        if not any(scene.id == scene_id for scene in room.scenes):
            raise SceneNotFoundError(scene_id, room_id)
        return room

    room = next(
        (item for item in rooms if any(scene.id == scene_id for scene in item.scenes)),
        None,
    )
    if room is None:
        raise SceneNotFoundError(scene_id)
    return room
