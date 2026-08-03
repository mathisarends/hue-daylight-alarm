import pytest
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.features.devices.application import (
    AudioOutputService,
    SwitchableAudioPlayer,
)
from huerise.features.devices.domain import AudioOutput
from huerise.features.devices.presentation import audio_output_router
from huerise.presentation import auth
from tests.application.conftest import make_audio

TOKEN = "test-access-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


class StubProvider(Provider):
    scope = Scope.REQUEST

    def __init__(self, player: SwitchableAudioPlayer) -> None:
        super().__init__()
        self._player = player

    @provide
    def audio_output_service(self) -> AudioOutputService:
        return AudioOutputService(self._player)


@pytest.fixture
def player() -> SwitchableAudioPlayer:
    return SwitchableAudioPlayer(
        {AudioOutput.LOCAL: make_audio(), AudioOutput.SONOS: make_audio()},
        active=AudioOutput.LOCAL,
    )


@pytest.fixture
def client(
    player: SwitchableAudioPlayer, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    monkeypatch.setattr(auth._settings, "access_token", SecretStr(TOKEN))

    app = FastAPI()
    app.include_router(audio_output_router)
    setup_dishka(make_async_container(StubProvider(player)), app=app)
    return TestClient(app)


def test_reports_the_active_output(client: TestClient) -> None:
    response = client.get("/audio-output", headers=AUTH)

    assert response.status_code == 200
    assert response.json() == {"active": "local", "available": ["local", "sonos"]}


def test_switches_the_output(client: TestClient, player: SwitchableAudioPlayer) -> None:
    response = client.put("/audio-output", headers=AUTH, json={"output": "sonos"})

    assert response.status_code == 200
    assert response.json()["active"] == "sonos"
    assert player.active is AudioOutput.SONOS


def test_rejects_an_unknown_output(client: TestClient) -> None:
    response = client.put("/audio-output", headers=AUTH, json={"output": "kitchen"})

    assert response.status_code == 422


def test_requires_the_access_token(client: TestClient) -> None:
    assert client.get("/audio-output").status_code == 401
