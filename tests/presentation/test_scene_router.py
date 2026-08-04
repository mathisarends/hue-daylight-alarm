from uuid import UUID

import pytest
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.features.devices.application import SceneService
from huerise.features.devices.domain import Room, Scene
from huerise.features.devices.presentation import (
    register_device_exception_handlers,
    scene_router,
)
from huerise.presentation import auth
from tests.application.conftest import make_lights

TOKEN = "test-access-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
ROOM_ID = UUID("11111111-1111-4111-8111-111111111111")
SCENE_ID = UUID("22222222-2222-4222-8222-222222222222")
BEDROOM = Room(
    id=ROOM_ID,
    name="Bedroom",
    scenes=(Scene(id=SCENE_ID, name="Relax"),),
)


class StubProvider(Provider):
    scope = Scope.REQUEST

    def __init__(self, service: SceneService) -> None:
        super().__init__()
        self._service = service

    @provide
    def scene_service(self) -> SceneService:
        return self._service


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(auth._settings, "access_token", SecretStr(TOKEN))
    lights = make_lights()
    lights.list_rooms.return_value = [BEDROOM]
    service = SceneService(lights)

    app = FastAPI()
    app.include_router(scene_router)
    register_device_exception_handlers(app)
    setup_dishka(make_async_container(StubProvider(service)), app=app)
    return TestClient(app)


def test_requires_the_access_token(client: TestClient) -> None:
    assert client.get("/rooms").status_code == 401


def test_lists_rooms_with_their_scenes(client: TestClient) -> None:
    response = client.get("/rooms", headers=AUTH)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(ROOM_ID),
            "name": "Bedroom",
            "scenes": [{"id": str(SCENE_ID), "name": "Relax"}],
        }
    ]


def test_gets_a_known_room(client: TestClient) -> None:
    response = client.get(f"/rooms/{ROOM_ID}", headers=AUTH)

    assert response.status_code == 200
    assert response.json()["name"] == "Bedroom"


def test_getting_an_unknown_room_returns_404(client: TestClient) -> None:
    unknown_id = UUID("33333333-3333-4333-8333-333333333333")
    response = client.get(f"/rooms/{unknown_id}", headers=AUTH)

    assert response.status_code == 404
    assert response.json() == {"detail": f"Room '{unknown_id}' not found"}


def test_activates_a_scene(client: TestClient) -> None:
    response = client.post(
        f"/rooms/{ROOM_ID}/scenes/{SCENE_ID}/activate",
        headers=AUTH,
        json={"brightness": 12.5},
    )

    assert response.status_code == 204


def test_activating_an_unknown_scene_returns_404(client: TestClient) -> None:
    unknown_id = UUID("33333333-3333-4333-8333-333333333333")
    response = client.post(
        f"/rooms/{ROOM_ID}/scenes/{unknown_id}/activate",
        headers=AUTH,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": f"Room '{ROOM_ID}' has no scene '{unknown_id}'"
    }
