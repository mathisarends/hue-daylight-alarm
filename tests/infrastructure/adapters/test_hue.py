from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from huerise.features.devices.infrastructure.hue import HueLights

ROOM_ID = UUID("11111111-1111-4111-8111-111111111111")
SCENE_ID = UUID("22222222-2222-4222-8222-222222222222")


def make_hue() -> MagicMock:
    hue = MagicMock()
    hue.rooms.list = AsyncMock()
    hue.rooms.scenes = AsyncMock()
    hue.rooms.set_brightness = AsyncMock()
    hue.scenes.activate = AsyncMock()
    return hue


async def test_lists_rooms_with_their_scenes() -> None:
    hue = make_hue()
    hue.rooms.list.return_value = SimpleNamespace(
        data=[SimpleNamespace(id=ROOM_ID, name="Bedroom")]
    )
    hue.rooms.scenes.return_value = [
        SimpleNamespace(id=SCENE_ID, name="Tageslichtwecker")
    ]

    rooms = await HueLights(hue).list_rooms()

    assert rooms[0].id == ROOM_ID
    assert rooms[0].scenes[0].id == SCENE_ID
    hue.rooms.scenes.assert_awaited_once_with(ROOM_ID)


async def test_activate_scene_is_forwarded_to_hueify() -> None:
    hue = make_hue()

    await HueLights(hue).activate_scene(SCENE_ID, brightness=12.5)

    hue.scenes.activate.assert_awaited_once_with(SCENE_ID, brightness=12.5)


async def test_set_brightness_is_forwarded_to_hueify() -> None:
    hue = make_hue()

    await HueLights(hue).set_brightness(ROOM_ID, 80.5)

    hue.rooms.set_brightness.assert_awaited_once_with(ROOM_ID, 80.5)
