from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from uuid import UUID

from huerise.features.lighting.domain import (
    HueBridge,
    HueBridgeSelection,
    LightChange,
    Room,
)
from huerise.lifecycle import Runnable

type LightChangeHandler = Callable[[LightChange], Awaitable[None]]


class HueConfigurator(ABC):
    @abstractmethod
    async def configure(self, selection: HueBridgeSelection) -> None: ...


class HueEnvironmentOverride(ABC):
    bridge_ip: str | None

    @property
    @abstractmethod
    def configured(self) -> bool: ...


class HueOnboarding(ABC):
    @abstractmethod
    async def discover(self) -> tuple[HueBridge, ...]: ...

    @abstractmethod
    async def register(self, bridge_ip: str) -> str: ...


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
