from abc import ABC, abstractmethod
from uuid import UUID

from huerise.features.devices.domain import Room


class AudioPlayer(ABC):
    @abstractmethod
    async def play(self, sound_id: UUID, volume: int) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def set_volume(self, volume: int) -> None: ...


class Lights(ABC):
    @abstractmethod
    async def list_rooms(self) -> list[Room]: ...

    @abstractmethod
    async def activate_scene(self, room_name: str, scene_name: str) -> None: ...

    @abstractmethod
    async def set_brightness(self, room_name: str, brightness: int) -> None: ...
