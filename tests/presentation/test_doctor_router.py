from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.features.lighting.application import (
    DoctorService,
    DoctorStatus,
    SetupCheck,
)
from huerise.features.lighting.presentation import doctor_router
from huerise.infrastructure.auth import encode_access_token
from huerise.presentation import auth

SECRET = "test-jwt-secret"
TOKEN = encode_access_token(
    user_id=uuid4(), tenant_id=uuid4(), secret=SECRET, ttl_minutes=15
)
AUTH = {"Authorization": f"Bearer {TOKEN}"}


class StubProvider(Provider):
    scope = Scope.REQUEST

    def __init__(self, service: DoctorService) -> None:
        super().__init__()
        self._service = service

    @provide
    def doctor_service(self) -> DoctorService:
        return self._service


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(auth._settings, "jwt_secret", SecretStr(SECRET))
    service = MagicMock(spec=DoctorService)
    service.check = AsyncMock(
        return_value=DoctorStatus(hue_bridge=SetupCheck(configured=True))
    )
    app = FastAPI()
    app.include_router(doctor_router)
    setup_dishka(make_async_container(StubProvider(service)), app=app)
    return TestClient(app)


def test_reports_hue_configuration(client: TestClient) -> None:
    response = client.get("/doctor", headers=AUTH)

    assert response.status_code == 200
    assert response.json() == {
        "configured": True,
        "hue_bridge": {"configured": True},
    }


def test_doctor_requires_api_authentication(client: TestClient) -> None:
    assert client.get("/doctor").status_code == 401
