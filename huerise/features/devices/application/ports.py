from abc import ABC, abstractmethod
from uuid import UUID

from huerise.features.devices.domain import Room


class AudioPlayer(ABC):
    @abstractmethod
    async def play(self, sound_id: UUID, volume: int) -> None:
        """Play a sound to the end.

        Callers rely on this returning only once the sound is over -- the
        runner finishes an occurrence when the ringtone stops. Start it as a
        task to keep playing in the background.
        """

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def set_volume(self, volume: int) -> None: ...


class Lights(ABC):
    @abstractmethod
    async def list_rooms(self) -> list[Room]: ...

    @abstractmethod
    async def activate_scene(
        self, scene_id: UUID, *, brightness: float | None = None
    ) -> None: ...

    @abstractmethod
    async def set_brightness(self, room_id: UUID, brightness: float) -> None: ...
