from datetime import UTC, datetime
from uuid import uuid4

import pytest
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.features.alarm.application import AlarmService
from huerise.features.alarm.domain import OccurrenceState
from huerise.features.alarm.presentation import (
    alarm_router,
    register_alarm_exception_handlers,
)
from huerise.infrastructure.auth import encode_access_token
from huerise.presentation import auth
from tests.application.conftest import (
    ROOM_ID,
    InMemoryAlarmRepository,
    InMemoryOccurrenceRepository,
    make_alarm,
    make_alarm_service,
    make_occurrence,
)

SECRET = "test-jwt-secret"
TOKEN = encode_access_token(
    user_id=uuid4(), tenant_id=uuid4(), secret=SECRET, ttl_minutes=15
)
AUTH = {"Authorization": f"Bearer {TOKEN}"}


class StubProvider(Provider):
    scope = Scope.REQUEST

    def __init__(self, service: AlarmService) -> None:
        super().__init__()
        self._service = service

    @provide
    def alarm_service(self) -> AlarmService:
        return self._service


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(auth._settings, "jwt_secret", SecretStr(SECRET))

    app = FastAPI()
    app.include_router(alarm_router)
    register_alarm_exception_handlers(app)
    setup_dishka(make_async_container(StubProvider(make_alarm_service())), app=app)
    return TestClient(app)


def _create_alarm(client: TestClient, **overrides) -> dict:
    body = {
        "label": "Morning",
        "schedule": {"hour": 7, "minute": 0},
        "room_id": str(ROOM_ID),
        "room_name": "Bedroom",
        **overrides,
    }
    response = client.post("/alarms", headers=AUTH, json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_requires_the_access_token(client: TestClient) -> None:
    assert client.get("/alarms").status_code == 401


def test_create_falls_back_to_the_default_profile(client: TestClient) -> None:
    alarm = _create_alarm(client)

    assert alarm["profile_id"] is not None


def test_full_lifecycle(client: TestClient) -> None:
    alarm = _create_alarm(client, label="Weekday")
    alarm_id = alarm["id"]

    assert client.get("/alarms", headers=AUTH).json() == [alarm]
    assert client.get(f"/alarms/{alarm_id}", headers=AUTH).json() == alarm

    updated = client.patch(
        f"/alarms/{alarm_id}", headers=AUTH, json={"label": "Weekend"}
    )
    assert updated.status_code == 200
    assert updated.json()["label"] == "Weekend"

    disabled = client.post(f"/alarms/{alarm_id}/disable", headers=AUTH)
    assert disabled.json()["is_enabled"] is False

    enabled = client.post(f"/alarms/{alarm_id}/enable", headers=AUTH)
    assert enabled.json()["is_enabled"] is True

    delete_response = client.delete(f"/alarms/{alarm_id}", headers=AUTH)
    assert delete_response.status_code == 204

    assert client.get(f"/alarms/{alarm_id}", headers=AUTH).status_code == 404


@pytest.mark.parametrize(
    "make_request",
    [
        lambda client, alarm_id: client.get(f"/alarms/{alarm_id}", headers=AUTH),
        lambda client, alarm_id: client.patch(
            f"/alarms/{alarm_id}", headers=AUTH, json={"label": "x"}
        ),
        lambda client, alarm_id: client.post(
            f"/alarms/{alarm_id}/enable", headers=AUTH
        ),
        lambda client, alarm_id: client.post(
            f"/alarms/{alarm_id}/dismiss", headers=AUTH
        ),
        lambda client, alarm_id: client.delete(f"/alarms/{alarm_id}", headers=AUTH),
    ],
)
def test_unknown_alarm_returns_404(client: TestClient, make_request) -> None:
    alarm_id = uuid4()

    response = make_request(client, alarm_id)

    assert response.status_code == 404
    assert response.json() == {"detail": f"Alarm {alarm_id} not found"}


def test_enabling_an_already_enabled_alarm_returns_409(client: TestClient) -> None:
    alarm = _create_alarm(client)

    response = client.post(f"/alarms/{alarm['id']}/enable", headers=AUTH)

    assert response.status_code == 409
    assert response.json() == {"detail": f"Alarm {alarm['id']} is already enabled"}


def test_snoozing_without_an_active_occurrence_returns_409(client: TestClient) -> None:
    alarm = _create_alarm(client)

    response = client.post(
        f"/alarms/{alarm['id']}/snooze", headers=AUTH, json={"minutes": 5}
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": f"Alarm {alarm['id']} has no active occurrence"
    }


@pytest.fixture
def ringing_alarm_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, str]:
    monkeypatch.setattr(auth._settings, "jwt_secret", SecretStr(SECRET))
    alarm = make_alarm()
    occurrence = make_occurrence(
        alarm.id, datetime.now(UTC), state=OccurrenceState.RINGING
    )
    service = make_alarm_service(
        alarms=InMemoryAlarmRepository([alarm]),
        occurrences=InMemoryOccurrenceRepository([occurrence]),
    )

    app = FastAPI()
    app.include_router(alarm_router)
    register_alarm_exception_handlers(app)
    setup_dishka(make_async_container(StubProvider(service)), app=app)
    return TestClient(app), str(alarm.id)


def test_snoozing_a_ringing_alarm_reschedules_it(
    ringing_alarm_client: tuple[TestClient, str],
) -> None:
    client, alarm_id = ringing_alarm_client

    response = client.post(
        f"/alarms/{alarm_id}/snooze", headers=AUTH, json={"minutes": 5}
    )

    assert response.status_code == 200
    assert response.json()["state"] == "snoozed"


def test_dismissing_a_ringing_alarm_stops_it(
    ringing_alarm_client: tuple[TestClient, str],
) -> None:
    client, alarm_id = ringing_alarm_client

    response = client.post(f"/alarms/{alarm_id}/dismiss", headers=AUTH)

    assert response.status_code == 200
    assert response.json()["state"] == "dismissed"


def test_lists_the_occurrences_for_an_alarm(
    ringing_alarm_client: tuple[TestClient, str],
) -> None:
    client, alarm_id = ringing_alarm_client

    response = client.get(f"/alarms/{alarm_id}/occurrences", headers=AUTH)

    assert response.status_code == 200
    [occurrence] = response.json()
    assert occurrence["state"] == "ringing"
