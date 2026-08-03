import pytest

from huerise.features.devices.application import SceneService
from huerise.features.devices.domain import (
    Room,
    RoomNotFoundError,
    SceneNotFoundError,
)
from tests.application.conftest import make_lights

BEDROOM = Room(name="Bedroom", scene_names=("Tageslichtwecker", "Relax"))


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

        await service.activate_scene("Bedroom", "Relax")

        lights.activate_scene.assert_awaited_once_with("Bedroom", "Relax")

    async def test_rejects_an_unknown_room(self) -> None:
        service, lights = make_scene_service()

        with pytest.raises(RoomNotFoundError):
            await service.activate_scene("Kitchen", "Relax")

        lights.activate_scene.assert_not_awaited()

    async def test_rejects_a_scene_the_room_does_not_have(self) -> None:
        service, lights = make_scene_service()

        with pytest.raises(SceneNotFoundError):
            await service.activate_scene("Bedroom", "Party")

        lights.activate_scene.assert_not_awaited()
