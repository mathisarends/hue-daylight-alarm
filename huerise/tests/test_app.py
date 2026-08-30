from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pytest
from dishka import Provider, Scope, make_async_container, provide
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.app import create_app
from huerise.configuration import APISettings, HueEnvironment, YamlConfiguration
from huerise.features.daylight_alarm.provider import DaylightAlarmProvider
from huerise.features.lighting.hue import (
    HueClientFactory,
    HueCredentials,
    Room,
    Scene,
)
from huerise.features.lighting.onboarding import (
    HueBridge,
    OnboardingGateway,
)
from huerise.features.lighting.provider import LightingProvider

API_KEY = "test-api-key"
AUTH = {"X-API-Key": API_KEY}
SCENE_ID = UUID(int=1)
ROOM_ID = UUID(int=2)


class StubHueClient:
    def __init__(self) -> None:
        self.commands: list[tuple] = []

    async def list_rooms(self) -> list[Room]:
        return [Room(ROOM_ID, "Bedroom", (Scene(SCENE_ID, "Sunrise"),))]

    async def activate_scene(self, scene_id: UUID, *, brightness: float) -> None:
        self.commands.append(("activate", scene_id, brightness))

    async def set_brightness(self, room_id: UUID, brightness: float) -> None:
        self.commands.append(("brightness", room_id, brightness))

    async def close(self) -> None:
        pass


class StubClientFactory:
    def __init__(self, client: StubHueClient) -> None:
        self.client = client

    def create(self, _: HueCredentials) -> StubHueClient:
        return self.client


class StubOnboardingGateway:
    async def discover(self) -> tuple[HueBridge, ...]:
        return (HueBridge("bridge-1", "192.0.2.10"),)

    async def register(self, bridge_ip: str) -> str:
        return "registered-hue-key-123"


class AppTestProvider(Provider):
    scope = Scope.APP

    def __init__(self, path: Path, client: StubHueClient) -> None:
        super().__init__()
        self._path = path
        self._client = client

    @provide
    def settings(self) -> APISettings:
        return APISettings(
            api_key=SecretStr(API_KEY), config_path=self._path, _env_file=None
        )

    @provide
    def environment(self) -> HueEnvironment:
        return HueEnvironment(_env_file=None)

    @provide
    def configuration(self) -> YamlConfiguration:
        return YamlConfiguration(self._path)

    @provide
    def clients(self) -> HueClientFactory:
        return StubClientFactory(self._client)

    @provide
    def onboarding_gateway(self) -> OnboardingGateway:
        return StubOnboardingGateway()


@pytest.fixture
def hue_client() -> StubHueClient:
    return StubHueClient()


@pytest.fixture
def client(tmp_path: Path, hue_client: StubHueClient) -> Iterator[TestClient]:
    path = tmp_path / "huerise.yml"
    path.write_text(
        f"""\
hue:
  bridge_id: bridge-1
  bridge_ip: 192.0.2.10
  app_key: a-valid-hue-app-key-123
daylight_alarm:
  scene_id: {SCENE_ID}
  start_brightness: 1
  end_brightness: 100
  duration_seconds: 1800
""",
        encoding="utf-8",
    )
    container = make_async_container(
        LightingProvider(),
        DaylightAlarmProvider(),
        AppTestProvider(path, hue_client),
    )
    with TestClient(create_app(container)) as test_client:
        yield test_client


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}])
def test_protected_routes_require_api_key(
    client: TestClient, headers: dict[str, str]
) -> None:
    assert client.post("/daylight-alarm/start", headers=headers).status_code == 401
    assert client.get("/doctor", headers=headers).status_code == 401
    assert client.get("/rooms", headers=headers).status_code == 401
    assert client.get("/hue/bridge", headers=headers).status_code == 401


def test_exposes_doctor_and_rooms(client: TestClient) -> None:
    doctor = client.get("/doctor", headers=AUTH)
    rooms = client.get("/rooms", headers=AUTH)

    assert doctor.status_code == 200
    assert [check["name"] for check in doctor.json()["checks"]] == [
        "configuration",
        "hue_credentials",
        "hue_bridge",
        "scene",
    ]
    assert rooms.json() == [
        {
            "id": str(ROOM_ID),
            "name": "Bedroom",
            "scenes": [{"id": str(SCENE_ID), "name": "Sunrise"}],
        }
    ]


def test_starts_and_stops_daylight_alarm(
    client: TestClient, hue_client: StubHueClient
) -> None:
    started = client.post("/daylight-alarm/start", headers=AUTH)
    stopped = client.post("/daylight-alarm/stop", headers=AUTH)

    assert started.status_code == 202
    assert stopped.status_code == 204
    assert hue_client.commands == [("activate", SCENE_ID, 1)]


def test_starts_and_stops_ten_second_demo(client: TestClient) -> None:
    path = f"/rooms/{ROOM_ID}/scenes/{SCENE_ID}/demo"

    started = client.post(path, headers=AUTH)
    stopped = client.delete(path, headers=AUTH)

    assert started.status_code == 202
    assert started.json() == {"status": "started", "duration_seconds": 10}
    assert stopped.status_code == 204


def test_exposes_onboarding_state(client: TestClient) -> None:
    response = client.get("/hue/bridge", headers=AUTH)

    assert response.status_code == 200
    assert response.json() == {
        "state": "ready",
        "bridge_id": "bridge-1",
        "ip_address": "192.0.2.10",
        "read_only": False,
    }


def test_supports_complete_client_onboarding_flow(client: TestClient) -> None:
    bridges = client.get("/hue/bridges", headers=AUTH)
    selected = client.put("/hue/bridge", headers=AUTH, json={"bridge_id": "bridge-1"})
    registered = client.post("/hue/bridge/register", headers=AUTH)

    assert bridges.status_code == 200
    assert bridges.json() == [
        {"id": "bridge-1", "ip_address": "192.0.2.10", "selected": True}
    ]
    assert selected.json()["state"] == "link_button_required"
    assert registered.json()["state"] == "ready"
