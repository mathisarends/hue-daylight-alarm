from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest
from pydantic import SecretStr

from huerise.configuration import HueConfig, YamlConfiguration
from huerise.env import HueEnvironment
from huerise.features.lighting.application import HueCredentials, HueUnavailableError
from huerise.features.lighting.infrastructure import (
    HueCredentialsProvider,
    HueifyClient,
    HueifyClientFactory,
    HueifyOnboarding,
)
from huerise.features.lighting.infrastructure import hue as hue_module

SCENE_ID = UUID(int=1)
ROOM_ID = UUID(int=2)


@dataclass
class FakeRoomsApi:
    brightness: list[tuple[UUID, float]] = field(default_factory=list)

    async def list(self) -> SimpleNamespace:
        return SimpleNamespace(data=[SimpleNamespace(id=ROOM_ID, name="Bedroom")])

    async def scenes(self, room_id: UUID) -> list[SimpleNamespace]:
        assert room_id == ROOM_ID
        return [SimpleNamespace(id=SCENE_ID, name="Sunrise")]

    async def set_brightness(self, room_id: UUID, brightness: float) -> None:
        self.brightness.append((room_id, brightness))


@dataclass
class FakeScenesApi:
    activations: list[tuple[UUID, float]] = field(default_factory=list)

    async def activate(self, scene_id: UUID, *, brightness: float) -> None:
        self.activations.append((scene_id, brightness))


@dataclass
class FakeHueify:
    rooms: FakeRoomsApi = field(default_factory=FakeRoomsApi)
    scenes: FakeScenesApi = field(default_factory=FakeScenesApi)
    closed: bool = False

    async def close(self) -> None:
        self.closed = True


def repository(tmp_path: Path) -> YamlConfiguration:
    return YamlConfiguration(tmp_path / "huerise.yml")


def test_credentials_prefer_environment_overrides(tmp_path: Path) -> None:
    environment = HueEnvironment(
        bridge_ip="192.0.2.20",
        app_key=SecretStr("environment-hue-key-123"),
        _env_file=None,
    )

    credentials = HueCredentialsProvider(repository(tmp_path), environment).get()

    assert credentials == HueCredentials("192.0.2.20", "environment-hue-key-123")


def test_credentials_load_saved_configuration(tmp_path: Path) -> None:
    configuration = repository(tmp_path)
    configuration.save_hue(
        HueConfig(
            bridge_ip="192.0.2.10",
            app_key="configured-hue-key-123",
        )
    )

    credentials = HueCredentialsProvider(
        configuration, HueEnvironment(_env_file=None)
    ).get()

    assert credentials == HueCredentials("192.0.2.10", "configured-hue-key-123")


@pytest.mark.parametrize(
    "hue",
    [None, HueConfig(bridge_ip="192.0.2.10")],
)
def test_credentials_require_a_registered_bridge(
    tmp_path: Path, hue: HueConfig | None
) -> None:
    configuration = repository(tmp_path)
    if hue is not None:
        configuration.save_hue(hue)

    with pytest.raises(HueUnavailableError, match="not configured"):
        HueCredentialsProvider(configuration, HueEnvironment(_env_file=None)).get()


def test_factory_builds_adapter_with_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_with: list[tuple[str, str]] = []
    external = FakeHueify()

    def fake_hueify(bridge_ip: str, app_key: str) -> FakeHueify:
        created_with.append((bridge_ip, app_key))
        return external

    monkeypatch.setattr(hue_module, "Hueify", fake_hueify)

    client = HueifyClientFactory().create(HueCredentials("192.0.2.10", "secret"))

    assert isinstance(client, HueifyClient)
    assert client._client is external
    assert created_with == [("192.0.2.10", "secret")]


async def test_client_adapts_hueify_operations() -> None:
    external = FakeHueify()
    client = HueifyClient(external)

    rooms = await client.list_rooms()
    await client.activate_scene(SCENE_ID, brightness=12.5)
    await client.set_brightness(ROOM_ID, 42)
    await client.close()

    assert [(room.id, room.name) for room in rooms] == [(ROOM_ID, "Bedroom")]
    assert [(scene.id, scene.name) for scene in rooms[0].scenes] == [
        (SCENE_ID, "Sunrise")
    ]
    assert external.scenes.activations == [(SCENE_ID, 12.5)]
    assert external.rooms.brightness == [(ROOM_ID, 42)]
    assert external.closed is True


async def test_onboarding_adapts_hueify_functions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registrations: list[tuple[str, str]] = []

    async def fake_discover() -> list[SimpleNamespace]:
        return [SimpleNamespace(id="bridge-1", internalipaddress="192.0.2.10")]

    async def fake_register(bridge_ip: str, *, device_type: str) -> str:
        registrations.append((bridge_ip, device_type))
        return "registered-hue-key-123"

    monkeypatch.setattr(hue_module, "discover_bridges", fake_discover)
    monkeypatch.setattr(hue_module, "register_app_key", fake_register)
    onboarding = HueifyOnboarding()

    bridges = await onboarding.discover()
    app_key = await onboarding.register("192.0.2.10")

    assert [(bridge.id, bridge.ip_address) for bridge in bridges] == [
        ("bridge-1", "192.0.2.10")
    ]
    assert app_key == "registered-hue-key-123"
    assert registrations == [("192.0.2.10", "huerise#backend")]
