from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.features.devices.application import (
    SonosSpeakerService,
    SonosSpeakerStatus,
)
from huerise.features.devices.domain import SonosSpeaker
from huerise.features.devices.presentation import audio_output_router
from huerise.infrastructure.auth import encode_access_token
from huerise.presentation import auth

SECRET = "test-jwt-secret"
TOKEN = encode_access_token(
    user_id=uuid4(), tenant_id=uuid4(), secret=SECRET, ttl_minutes=15
)
AUTH = {"Authorization": f"Bearer {TOKEN}"}


class StubProvider(Provider):
    scope = Scope.REQUEST

    def __init__(self, service: SonosSpeakerService) -> None:
        super().__init__()
        self._service = service

    @provide
    def sonos_speaker_service(self) -> SonosSpeakerService:
        return self._service


@pytest.fixture
def service() -> MagicMock:
    speaker = SonosSpeaker(
        id="RINCON_BEDROOM",
        name="Bedroom",
        ip_address="192.168.1.42",
        group_id="GROUP_1",
        is_coordinator=True,
    )
    service = MagicMock(spec=SonosSpeakerService)
    service.discover = AsyncMock(
        return_value=(SonosSpeakerStatus(speaker=speaker, selected=False),)
    )
    service.select = AsyncMock(
        return_value=SonosSpeakerStatus(speaker=speaker, selected=True)
    )
    return service


@pytest.fixture
def client(service: SonosSpeakerService, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(auth._settings, "jwt_secret", SecretStr(SECRET))
    app = FastAPI()
    app.include_router(audio_output_router)
    setup_dishka(make_async_container(StubProvider(service)), app=app)
    return TestClient(app)


def test_lists_discovered_sonos_speakers(
    client: TestClient, service: MagicMock
) -> None:
    response = client.get("/audio-output/sonos/speakers", headers=AUTH)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "RINCON_BEDROOM",
            "name": "Bedroom",
            "ip_address": "192.168.1.42",
            "group_id": "GROUP_1",
            "is_coordinator": True,
            "selected": False,
        }
    ]
    service.discover.assert_awaited_once()


def test_selects_sonos_speaker(client: TestClient, service: MagicMock) -> None:
    response = client.put(
        "/audio-output/sonos/speaker",
        headers=AUTH,
        json={"speaker_id": "RINCON_BEDROOM"},
    )

    assert response.status_code == 200
    assert response.json()["selected"] is True
    service.select.assert_awaited_once_with("RINCON_BEDROOM")
