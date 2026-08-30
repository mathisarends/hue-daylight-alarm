from dataclasses import dataclass, field
from uuid import UUID

from huerise.features.lighting.application import (
    HueBridge,
    HueCredentials,
    Room,
)


@dataclass
class FakeHueClient:
    rooms: list[Room] = field(default_factory=list)
    list_rooms_error: Exception | None = None
    activate_scene_error: Exception | None = None
    set_brightness_error: Exception | None = None
    close_error: Exception | None = None
    commands: list[tuple[str, UUID, float]] = field(default_factory=list)
    closed: bool = False

    async def list_rooms(self) -> list[Room]:
        if self.list_rooms_error is not None:
            raise self.list_rooms_error
        return self.rooms

    async def activate_scene(self, scene_id: UUID, *, brightness: float) -> None:
        if self.activate_scene_error is not None:
            raise self.activate_scene_error
        self.commands.append(("activate", scene_id, brightness))

    async def set_brightness(self, room_id: UUID, brightness: float) -> None:
        if self.set_brightness_error is not None:
            raise self.set_brightness_error
        self.commands.append(("brightness", room_id, brightness))

    async def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


@dataclass
class FakeHueClientFactory:
    client: FakeHueClient
    error: Exception | None = None
    credentials: list[HueCredentials] = field(default_factory=list)

    def create(self, credentials: HueCredentials) -> FakeHueClient:
        self.credentials.append(credentials)
        if self.error is not None:
            raise self.error
        return self.client


@dataclass
class FakeHueCredentialsSource:
    credentials: HueCredentials = field(
        default_factory=lambda: HueCredentials("192.0.2.10", "secret")
    )
    error: Exception | None = None

    def get(self) -> HueCredentials:
        if self.error is not None:
            raise self.error
        return self.credentials


@dataclass
class FakeOnboardingGateway:
    bridges: tuple[HueBridge, ...] = ()
    app_key: str = "registered-hue-key-123"
    discovery_error: Exception | None = None
    registration_error: Exception | None = None
    registrations: list[str] = field(default_factory=list)

    async def discover(self) -> tuple[HueBridge, ...]:
        if self.discovery_error is not None:
            raise self.discovery_error
        return self.bridges

    async def register(self, bridge_ip: str) -> str:
        self.registrations.append(bridge_ip)
        if self.registration_error is not None:
            raise self.registration_error
        return self.app_key
