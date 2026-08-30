from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from huerise.app import AppServices, create_app
from huerise.configuration import ConfigurationError, ConfigurationIssue
from huerise.daylight_alarm import AlarmAlreadyRunningError
from huerise.hue import HueUnavailableError, SceneNotFoundError

API_KEY = "test-api-key"
AUTH = {"X-API-Key": API_KEY}


@pytest.fixture
def alarm() -> AsyncMock:
    alarm = AsyncMock()
    alarm.start.return_value = None
    alarm.stop.return_value = None
    return alarm


@pytest.fixture
def client(alarm: AsyncMock) -> TestClient:
    return TestClient(create_app(AppServices(API_KEY, alarm)))


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}])
def test_daylight_alarm_requires_api_key(
    client: TestClient, alarm: AsyncMock, headers: dict[str, str]
) -> None:
    response = client.post("/daylight-alarm/start", headers=headers)

    assert response.status_code == 401
    alarm.start.assert_not_awaited()


def test_starts_daylight_alarm(client: TestClient, alarm: AsyncMock) -> None:
    response = client.post("/daylight-alarm/start", headers=AUTH)

    assert response.status_code == 202
    assert response.json() == {"status": "started"}
    alarm.start.assert_awaited_once_with()


def test_stops_daylight_alarm(client: TestClient, alarm: AsyncMock) -> None:
    response = client.post("/daylight-alarm/stop", headers=AUTH)

    assert response.status_code == 204
    assert response.content == b""
    alarm.stop.assert_awaited_once_with()


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (AlarmAlreadyRunningError("running"), 409),
        (SceneNotFoundError(UUID(int=1)), 404),
        (HueUnavailableError("unavailable"), 503),
    ],
)
def test_maps_domain_errors(
    client: TestClient,
    alarm: AsyncMock,
    error: Exception,
    expected_status: int,
) -> None:
    alarm.start.side_effect = error

    response = client.post("/daylight-alarm/start", headers=AUTH)

    assert response.status_code == expected_status
    assert response.json()["detail"] == str(error)


def test_returns_configuration_issues(
    client: TestClient,
    alarm: AsyncMock,
) -> None:
    alarm.start.side_effect = ConfigurationError(
        "Configuration is invalid",
        [
            ConfigurationIssue(
                location="daylight_alarm.scene_id", message="bad", type="x"
            )
        ],
    )

    response = client.post("/daylight-alarm/start", headers=AUTH)

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Configuration is invalid",
        "issues": [
            {"location": "daylight_alarm.scene_id", "message": "bad", "type": "x"}
        ],
    }
