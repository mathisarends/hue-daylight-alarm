from unittest.mock import AsyncMock, MagicMock

import pytest
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.features.devices.application import (
    DiscoveredHueBridge,
    HueBridgeService,
    HueBridgeStatus,
    HueConfigurationSource,
)
from huerise.features.devices.domain import HueBridge, HueBridgeNotSelectedError
from huerise.features.devices.presentation import (
    hue_router,
    register_device_exception_handlers,
)
from huerise.presentation import auth

TOKEN = "test-access-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


class StubProvider(Provider):
    scope = Scope.REQUEST

    def __init__(self, service: HueBridgeService) -> None:
        super().__init__()
        self._service = service

    @provide
    def hue_bridge_service(self) -> HueBridgeService:
        return self._service


@pytest.fixture
def service() -> MagicMock:
    status = HueBridgeStatus(
        bridge_id="bridge-1",
        ip_address="10.0.0.2",
        configured=False,
        source=HueConfigurationSource.DATABASE,
    )
    service = MagicMock(spec=HueBridgeService)
    service.status = AsyncMock(return_value=status)
    service.discover = AsyncMock(
        return_value=(
            DiscoveredHueBridge(HueBridge("bridge-1", "10.0.0.2"), True),
        )
    )
    service.select = AsyncMock(return_value=status)
    service.register = AsyncMock(
        return_value=HueBridgeStatus(
            bridge_id="bridge-1",
            ip_address="10.0.0.2",
            configured=True,
            source=HueConfigurationSource.DATABASE,
        )
    )
    return service


@pytest.fixture
def client(service: HueBridgeService, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(auth._settings, "access_token", SecretStr(TOKEN))
    app = FastAPI()
    app.include_router(hue_router)
    register_device_exception_handlers(app)
    setup_dishka(make_async_container(StubProvider(service)), app=app)
    return TestClient(app)


def test_lists_discovered_bridges(client: TestClient) -> None:
    response = client.get("/hue/bridges", headers=AUTH)

    assert response.status_code == 200
    assert response.json() == [
        {"id": "bridge-1", "ip_address": "10.0.0.2", "selected": True}
    ]


def test_selects_bridge_by_stable_id(client: TestClient, service: MagicMock) -> None:
    response = client.put(
        "/hue/bridge", headers=AUTH, json={"bridge_id": "bridge-1"}
    )

    assert response.status_code == 200
    service.select.assert_awaited_once_with("bridge-1")


def test_registers_without_returning_app_key(
    client: TestClient, service: MagicMock
) -> None:
    response = client.post("/hue/bridge/register", headers=AUTH)

    assert response.status_code == 200
    assert response.json() == {
        "bridge_id": "bridge-1",
        "ip_address": "10.0.0.2",
        "configured": True,
        "source": "database",
    }
    assert "key" not in response.text
    service.register.assert_awaited_once()


def test_requires_api_authentication(client: TestClient) -> None:
    assert client.get("/hue/bridge").status_code == 401


def test_maps_missing_selection_to_conflict(
    client: TestClient, service: MagicMock
) -> None:
    service.register.side_effect = HueBridgeNotSelectedError()

    response = client.post("/hue/bridge/register", headers=AUTH)

    assert response.status_code == 409
