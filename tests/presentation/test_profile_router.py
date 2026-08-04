from uuid import uuid4

import pytest
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.features.alarm.application import AlarmProfileService
from huerise.features.alarm.presentation import (
    profile_router,
    register_alarm_exception_handlers,
)
from huerise.presentation import auth
from tests.application.conftest import SCENE_ID, InMemoryProfileRepository, make_profile

TOKEN = "test-access-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


class StubProvider(Provider):
    scope = Scope.REQUEST

    def __init__(self, service: AlarmProfileService) -> None:
        super().__init__()
        self._service = service

    @provide
    def profile_service(self) -> AlarmProfileService:
        return self._service


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(auth._settings, "access_token", SecretStr(TOKEN))
    service = AlarmProfileService(InMemoryProfileRepository([make_profile()]))

    app = FastAPI()
    app.include_router(profile_router)
    register_alarm_exception_handlers(app)
    setup_dishka(make_async_container(StubProvider(service)), app=app)
    return TestClient(app)


def test_requires_the_access_token(client: TestClient) -> None:
    assert client.get("/alarm-profiles").status_code == 401


def test_lists_the_existing_profile(client: TestClient) -> None:
    response = client.get("/alarm-profiles", headers=AUTH)

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Standard"


def test_creates_a_profile(client: TestClient) -> None:
    body = {
        "name": "Weekend",
        "intro": {"sound_id": str(uuid4())},
        "ringtone": {"sound_id": str(uuid4())},
        "sunrise": {
            "scene_id": str(SCENE_ID),
            "scene_name": "Tageslichtwecker",
        },
    }

    response = client.post("/alarm-profiles", headers=AUTH, json=body)

    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Weekend"
    assert created["sunrise"]["duration_minutes"] == 7

    listed = client.get("/alarm-profiles", headers=AUTH).json()
    assert created in listed


def test_deletes_a_profile(client: TestClient) -> None:
    profile = client.get("/alarm-profiles", headers=AUTH).json()[0]

    response = client.delete(f"/alarm-profiles/{profile['id']}", headers=AUTH)

    assert response.status_code == 204
    assert client.get("/alarm-profiles", headers=AUTH).json() == []


def test_deleting_an_unknown_profile_returns_404(client: TestClient) -> None:
    unknown_id = uuid4()

    response = client.delete(f"/alarm-profiles/{unknown_id}", headers=AUTH)

    assert response.status_code == 404
    assert response.json() == {"detail": f"Alarm profile {unknown_id} not found"}
