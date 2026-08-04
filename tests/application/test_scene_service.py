from uuid import uuid4

import pytest

from huerise.features.devices.application import SceneService
from huerise.features.devices.domain import (
    Room,
    RoomNotFoundError,
    Scene,
    SceneNotFoundError,
)
from tests.application.conftest import ROOM_ID, SCENE_ID, make_lights

RELAX_ID = SCENE_ID
BEDROOM = Room(
    id=ROOM_ID,
    name="Bedroom",
    scenes=(Scene(id=RELAX_ID, name="Relax"),),
)


def make_scene_service() -> tuple[SceneService, object]:
    lights = make_lights()
    lights.list_rooms.return_value = [BEDROOM]
    return SceneService(lights), lights


class TestSceneService:
    async def test_lists_rooms_with_their_scenes(self) -> None:
        service, _ = make_scene_service()

        assert await service.list_rooms() == [BEDROOM]

    async def test_activates_a_scene_of_the_room(self) -> None:
        service, lights = make_scene_service()

        await service.activate_scene(ROOM_ID, RELAX_ID, brightness=12.5)

        lights.activate_scene.assert_awaited_once_with(RELAX_ID, brightness=12.5)

    async def test_rejects_an_unknown_room(self) -> None:
        service, lights = make_scene_service()

        with pytest.raises(RoomNotFoundError):
            await service.activate_scene(uuid4(), RELAX_ID)

        lights.activate_scene.assert_not_awaited()

    async def test_rejects_a_scene_the_room_does_not_have(self) -> None:
        service, lights = make_scene_service()

        with pytest.raises(SceneNotFoundError):
            await service.activate_scene(ROOM_ID, uuid4())

        lights.activate_scene.assert_not_awaited()
