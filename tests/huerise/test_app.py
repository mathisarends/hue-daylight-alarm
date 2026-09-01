from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pytest
from dishka import Provider, Scope, make_async_container, provide
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise import __version__
from huerise.configuration import YamlConfiguration
from huerise.env import AppSettings, HueEnvironment
from huerise.features.daylight_alarm.infrastructure import DaylightAlarmProvider
from huerise.features.lighting.application import (
    HueBridge,
    HueClientFactory,
    OnboardingGateway,
    Room,
    Scene,
)
from huerise.features.lighting.infrastructure import LightingProvider
from huerise.main import create_app
from tests.huerise.features.lighting.fakes import (
    FakeHueClient,
    FakeHueClientFactory,
    FakeOnboardingGateway,
)

API_KEY = "test-api-key"
AUTH = {"X-API-Key": API_KEY}
SCENE_ID = UUID(int=1)
ROOM_ID = UUID(int=2)
OTHER_ROOM_ID = UUID(int=3)
OTHER_SCENE_ID = UUID(int=4)


class AppTestProvider(Provider):
    scope = Scope.APP

    def __init__(self, path: Path, client: FakeHueClient) -> None:
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
        return FakeHueClientFactory(self._client)

    @provide
    def onboarding_gateway(self) -> OnboardingGateway:
        return FakeOnboardingGateway((HueBridge("bridge-1", "192.0.2.10"),))


@pytest.fixture
def hue_client() -> FakeHueClient:
    return FakeHueClient([Room(ROOM_ID, "Bedroom", (Scene(SCENE_ID, "Sunrise", 80),))])


def _client(tmp_path: Path, hue_client: FakeHueClient) -> Iterator[TestClient]:
    path = tmp_path / "huerise.yml"
    path.write_text(
        f"""\
hue:
  bridge_id: bridge-1
  bridge_ip: 192.0.2.10
  app_key: a-valid-hue-app-key-123
daylight_alarm:
  room:
    id: {ROOM_ID}
    name: Bedroom
  scene:
    id: {SCENE_ID}
    name: Sunrise
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


@pytest.fixture
def client(tmp_path: Path, hue_client: FakeHueClient) -> Iterator[TestClient]:
    yield from _client(tmp_path, hue_client)


@pytest.fixture
def two_room_client(tmp_path: Path) -> Iterator[TestClient]:
    hue_client = FakeHueClient(
        [
            Room(ROOM_ID, "Bedroom", (Scene(SCENE_ID, "Sunrise", 80),)),
            Room(OTHER_ROOM_ID, "Kitchen", (Scene(OTHER_SCENE_ID, "Bright", 100),)),
        ]
    )
    yield from _client(tmp_path, hue_client)


def test_operation_ids_are_explicit_and_stable(client: TestClient) -> None:
    operations = {
        operation["operationId"]
        for path in client.app.openapi()["paths"].values()
        for operation in path.values()
    }

    assert operations == {
        "doctor",
        "getHueBridge",
        "getDaylightAlarmConfiguration",
        "listHueBridges",
        "listScenes",
        "registerHueBridge",
        "selectHueBridge",
        "setDaylightAlarmConfiguration",
        "startDaylightAlarm",
        "stopDaylightAlarm",
    }


def test_api_uses_package_version(client: TestClient) -> None:
    assert client.app.version == __version__


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
    assert client.get("/scenes", headers=headers).status_code == 401
    assert (
        client.get("/daylight-alarm/configuration", headers=headers).status_code == 401
    )
    assert client.get("/hue/bridge", headers=headers).status_code == 401


def test_exposes_doctor_scenes_and_configuration(client: TestClient) -> None:
    doctor = client.get("/doctor", headers=AUTH)
    scenes = client.get("/scenes", headers=AUTH)
    configuration = client.get("/daylight-alarm/configuration", headers=AUTH)

    assert doctor.status_code == 200
    assert [check["name"] for check in doctor.json()["checks"]] == [
        "configuration",
        "hue_credentials",
        "hue_bridge",
        "scene",
    ]
    assert scenes.json() == [
        {
            "id": str(SCENE_ID),
            "name": "Sunrise",
            "room_id": str(ROOM_ID),
            "room_name": "Bedroom",
            "brightness": 80.0,
        }
    ]
    assert configuration.json() == {
        "room": {"id": str(ROOM_ID), "name": "Bedroom"},
        "scene": {"id": str(SCENE_ID), "name": "Sunrise"},
        "duration_seconds": 1800,
        "after_alarm": None,
    }


def test_saves_configuration_from_the_selected_scene(client: TestClient) -> None:
    response = client.put(
        "/daylight-alarm/configuration",
        headers=AUTH,
        json={
            "room_id": str(ROOM_ID),
            "scene_id": str(SCENE_ID),
            "duration_seconds": 900,
            "after_alarm": {
                "room_id": str(ROOM_ID),
                "scene_id": str(SCENE_ID),
                "delay_seconds": 60,
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "room": {"id": str(ROOM_ID), "name": "Bedroom"},
        "scene": {"id": str(SCENE_ID), "name": "Sunrise"},
        "duration_seconds": 900,
        "after_alarm": {
            "room": {"id": str(ROOM_ID), "name": "Bedroom"},
            "scene": {"id": str(SCENE_ID), "name": "Sunrise"},
            "delay_seconds": 60,
        },
    }


def test_rejects_a_scene_from_another_room(two_room_client: TestClient) -> None:
    response = two_room_client.put(
        "/daylight-alarm/configuration",
        headers=AUTH,
        json={
            "room_id": str(ROOM_ID),
            "scene_id": str(OTHER_SCENE_ID),
            "duration_seconds": 900,
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": f"Hue scene {OTHER_SCENE_ID} does not belong to room {ROOM_ID}"
    }


def test_rejects_an_after_alarm_scene_from_another_room(
    two_room_client: TestClient,
) -> None:
    response = two_room_client.put(
        "/daylight-alarm/configuration",
        headers=AUTH,
        json={
            "room_id": str(ROOM_ID),
            "scene_id": str(SCENE_ID),
            "duration_seconds": 900,
            "after_alarm": {
                "room_id": str(ROOM_ID),
                "scene_id": str(OTHER_SCENE_ID),
                "delay_seconds": 60,
            },
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": f"Hue scene {OTHER_SCENE_ID} does not belong to room {ROOM_ID}"
    }


def test_rejects_an_unknown_scene(two_room_client: TestClient) -> None:
    unknown_scene_id = UUID(int=5)
    response = two_room_client.put(
        "/daylight-alarm/configuration",
        headers=AUTH,
        json={
            "room_id": str(ROOM_ID),
            "scene_id": str(unknown_scene_id),
            "duration_seconds": 900,
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Hue scene not found: {unknown_scene_id}"}


def test_starts_and_stops_daylight_alarm(
    client: TestClient, hue_client: FakeHueClient
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


def test_request_validation_matches_documented_error(client: TestClient) -> None:
    response = client.post(
        "/daylight-alarm/start",
        headers=AUTH,
        json={"duration_seconds": 0},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Request validation failed",
        "issues": [
            {
                "location": "body.duration_seconds",
                "message": "Input should be greater than or equal to 1",
                "type": "greater_than_equal",
            }
        ],
    }


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
