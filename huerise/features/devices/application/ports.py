from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Protocol
from uuid import UUID

from huerise.features.devices.domain import (
    HueBridge,
    HueBridgeSelection,
    LightChange,
    Room,
    SonosSpeaker,
)
from huerise.lifecycle import Runnable

type LightChangeHandler = Callable[[LightChange], Awaitable[None]]


class HueConfigurator(Protocol):
    async def configure(self, selection: HueBridgeSelection) -> None: ...


class HueEnvironmentOverride(Protocol):
    bridge_ip: str | None

    @property
    def configured(self) -> bool: ...


class HueOnboarding(Protocol):
    async def discover(self) -> tuple[HueBridge, ...]: ...

    async def register(self, bridge_ip: str) -> str: ...


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


class SonosSpeakerSelector(ABC):
    @property
    @abstractmethod
    def selected_speaker(self) -> SonosSpeaker | None: ...

    @abstractmethod
    async def discover_speakers(self) -> tuple[SonosSpeaker, ...]: ...

    @abstractmethod
    async def select_speaker(self, speaker_id: str) -> SonosSpeaker: ...

    @abstractmethod
    async def restore_speaker(self, speaker: SonosSpeaker) -> SonosSpeaker: ...


class Lights(ABC):
    @abstractmethod
    async def list_rooms(self) -> list[Room]: ...

    @abstractmethod
    async def activate_scene(
        self, scene_id: UUID, *, brightness: float | None = None
    ) -> None: ...

    @abstractmethod
    async def set_brightness(self, room_id: UUID, brightness: float) -> None: ...


class LightEvents(ABC, Runnable):
    """Rooms and scenes changing on the bridge, pushed as they happen."""

    @abstractmethod
    def subscribe(self, handler: LightChangeHandler) -> None: ...

    @abstractmethod
    def unsubscribe(self, handler: LightChangeHandler) -> None: ...

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...
