from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pytest
from dishka import Provider, Scope, make_async_container, provide
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.configuration import YamlConfiguration
from huerise.env import AppSettings, HueEnvironment
from huerise.features.daylight_alarm.infrastructure import DaylightAlarmProvider
from huerise.features.lighting.application import (
    HueBridge,
    HueClientFactory,
    HueCredentials,
    OnboardingGateway,
    Room,
    Scene,
)
from huerise.features.lighting.infrastructure import LightingProvider
from huerise.main import create_app

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
    def settings(self) -> AppSettings:
        return AppSettings(
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


def test_operation_ids_are_explicit_and_stable(client: TestClient) -> None:
    operations = {
        operation["operationId"]
        for path in client.app.openapi()["paths"].values()
        for operation in path.values()
    }

    assert operations == {
        "doctor",
        "getHueBridge",
        "listHueBridges",
        "listRooms",
        "listScenes",
        "registerHueBridge",
        "selectHueBridge",
        "startDaylightAlarm",
        "stopDaylightAlarm",
    }


def test_errors_are_documented_on_their_routes(client: TestClient) -> None:
    responses = client.app.openapi()["paths"]["/daylight-alarm/start"]["post"][
        "responses"
    ]

    assert responses["404"]["description"] == (
        "The configured Hue scene does not exist."
    )
    assert responses["409"]["description"] == ("A daylight alarm is already running.")
    assert responses["422"]["description"] == (
        "The YAML configuration is missing or invalid."
    )
    assert responses["503"]["description"] == (
        "The Hue Bridge is not configured, reachable, or authenticated."
    )


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
    scenes = client.get("/scenes", headers=AUTH)

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
    assert scenes.json() == [
        {
            "id": str(SCENE_ID),
            "name": "Sunrise",
            "room_id": str(ROOM_ID),
            "room_name": "Bedroom",
        }
    ]


def test_starts_and_stops_daylight_alarm(
    client: TestClient, hue_client: StubHueClient
) -> None:
    started = client.post("/daylight-alarm/start", headers=AUTH)
    stopped = client.post("/daylight-alarm/stop", headers=AUTH)

    assert started.status_code == 202
    assert started.json() == {"status": "started", "duration_seconds": 1800}
    assert stopped.status_code == 204
    assert hue_client.commands == [("activate", SCENE_ID, 1)]


def test_overrides_duration_for_one_run(client: TestClient) -> None:
    started = client.post(
        "/daylight-alarm/start",
        headers=AUTH,
        json={"duration_seconds": 10},
    )
    stopped = client.post("/daylight-alarm/stop", headers=AUTH)

    assert started.status_code == 202
    assert started.json() == {"status": "started", "duration_seconds": 10}
    assert stopped.status_code == 204


def test_rejects_a_second_alarm_with_the_documented_error(client: TestClient) -> None:
    first = client.post("/daylight-alarm/start", headers=AUTH)
    second = client.post("/daylight-alarm/start", headers=AUTH)
    client.post("/daylight-alarm/stop", headers=AUTH)

    assert first.status_code == 202
    assert second.status_code == 409
    assert second.json() == {"detail": "Daylight alarm is already running"}


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
