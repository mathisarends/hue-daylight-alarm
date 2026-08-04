from uuid import UUID

import pytest
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.features.devices.application import SoundService
from huerise.features.devices.presentation import (
    register_device_exception_handlers,
    sound_router,
)
from huerise.presentation import auth
from tests.application.conftest import InMemorySoundRepository, make_audio, make_sounds

TOKEN = "test-access-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
KNOWN_SOUND_ID = UUID("1693baba-146e-5b14-acf2-6f76554f36e9")


class StubProvider(Provider):
    scope = Scope.REQUEST

    def __init__(self, service: SoundService) -> None:
        super().__init__()
        self._service = service

    @provide
    def sound_service(self) -> SoundService:
        return self._service


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(auth._settings, "access_token", SecretStr(TOKEN))
    service = SoundService(InMemorySoundRepository(make_sounds()), make_audio())

    app = FastAPI()
    app.include_router(sound_router)
    register_device_exception_handlers(app)
    setup_dishka(make_async_container(StubProvider(service)), app=app)
    with TestClient(app) as test_client:
        yield test_client


def test_requires_the_access_token(client: TestClient) -> None:
    assert client.get("/sounds").status_code == 401


def test_lists_all_sounds(client: TestClient) -> None:
    response = client.get("/sounds", headers=AUTH)

    assert response.status_code == 200
    assert len(response.json()) == len(make_sounds())


def test_filters_sounds_by_category(client: TestClient) -> None:
    response = client.get("/sounds", headers=AUTH, params={"category": "get_up"})

    assert response.status_code == 200
    assert [sound["category"] for sound in response.json()] == ["get_up"]


def test_previews_a_known_sound(client: TestClient) -> None:
    response = client.post(
        "/sounds/preview", headers=AUTH, json={"sound_id": str(KNOWN_SOUND_ID)}
    )

    assert response.status_code == 202
    assert response.json()["id"] == str(KNOWN_SOUND_ID)


def test_previewing_an_unknown_sound_returns_404(client: TestClient) -> None:
    unknown_id = UUID("00000000-0000-0000-0000-000000000000")

    response = client.post(
        "/sounds/preview", headers=AUTH, json={"sound_id": str(unknown_id)}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Sound {unknown_id} not found"}


def test_stops_playback(client: TestClient) -> None:
    assert client.post("/sounds/stop", headers=AUTH).status_code == 204


def test_sets_the_volume(client: TestClient) -> None:
    response = client.post("/sounds/volume", headers=AUTH, json={"volume": 40})

    assert response.status_code == 204
