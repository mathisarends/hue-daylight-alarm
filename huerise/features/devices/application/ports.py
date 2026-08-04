from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from uuid import UUID

from huerise.features.devices.domain import LightChange, Room

type LightChangeHandler = Callable[[LightChange], Awaitable[None]]


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


class LightEvents(ABC):
    """Rooms and scenes changing on the bridge, pushed as they happen.

    Keeps the rest of the application from knowing that these arrive over an
    SSE connection, so that anything holding denormalised Hue names can react
    without depending on the vendor client.
    """

    @abstractmethod
    def subscribe(self, handler: LightChangeHandler) -> None: ...

    @abstractmethod
    async def start(self) -> None:
        """Open the connection and begin delivering changes to subscribers."""
