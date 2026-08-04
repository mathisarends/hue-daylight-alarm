from unittest.mock import AsyncMock, MagicMock

from huerise.features.devices.infrastructure.hue import HueLights


def make_hue() -> MagicMock:
    hue = MagicMock()
    hue.rooms.activate_scene = AsyncMock()
    hue.rooms.set_brightness = AsyncMock()
    return hue


async def test_lists_rooms_with_their_scenes() -> None:
    hue = make_hue()
    hue.rooms.names = ["Bedroom", "Kitchen"]
    hue.rooms.scene_names.side_effect = lambda name: {
        "Bedroom": ["Tageslichtwecker", "Relax"],
        "Kitchen": ["Bright"],
    }[name]

    rooms = await HueLights(hue).list_rooms()

    assert [(room.name, room.scene_names) for room in rooms] == [
        ("Bedroom", ("Tageslichtwecker", "Relax")),
        ("Kitchen", ("Bright",)),
    ]


async def test_activate_scene_is_forwarded_to_hueify() -> None:
    hue = make_hue()

    await HueLights(hue).activate_scene("Bedroom", "Relax")

    hue.rooms.activate_scene.assert_awaited_once_with("Bedroom", "Relax")


async def test_set_brightness_is_forwarded_to_hueify() -> None:
    hue = make_hue()

    await HueLights(hue).set_brightness("Bedroom", 80)

    hue.rooms.set_brightness.assert_awaited_once_with("Bedroom", 80)
