from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from hueify.models import (
    DimmingState,
    LightUpdate,
    OnState,
    ResourceReference,
    ResourceType,
    SceneActionTarget,
    SceneMetadata,
)
from hueify.models import (
    Scene as HueScene,
)

from huerise.features.devices.infrastructure.hue import HueLights

ROOM_ID = UUID("11111111-1111-4111-8111-111111111111")
SCENE_ID = UUID("22222222-2222-4222-8222-222222222222")


def make_scene() -> HueScene:
    return HueScene(
        id=SCENE_ID,
        metadata=SceneMetadata(name="Tageslichtwecker"),
        group=ResourceReference(rid=ROOM_ID, rtype=ResourceType.ROOM),
        actions=[
            SceneActionTarget(
                target=ResourceReference(rid=uuid4(), rtype=ResourceType.LIGHT),
                action=LightUpdate(
                    on=OnState(on=True), dimming=DimmingState(brightness=60)
                ),
            ),
            SceneActionTarget(
                target=ResourceReference(rid=uuid4(), rtype=ResourceType.LIGHT),
                action=LightUpdate(
                    on=OnState(on=True), dimming=DimmingState(brightness=80)
                ),
            ),
            SceneActionTarget(
                target=ResourceReference(rid=uuid4(), rtype=ResourceType.LIGHT),
                action=LightUpdate(
                    on=OnState(on=False), dimming=DimmingState(brightness=20)
                ),
            ),
        ],
    )


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
    hue.rooms.scenes.return_value = [make_scene()]

    rooms = await HueLights(hue).list_rooms()

    assert rooms[0].id == ROOM_ID
    assert rooms[0].scenes[0].id == SCENE_ID
    assert rooms[0].scenes[0].brightness == 70
    hue.rooms.scenes.assert_awaited_once_with(ROOM_ID)


async def test_activate_scene_is_forwarded_to_hueify() -> None:
    hue = make_hue()

    await HueLights(hue).activate_scene(SCENE_ID, brightness=12.5)

    hue.scenes.activate.assert_awaited_once_with(SCENE_ID, brightness=12.5)


async def test_set_brightness_is_forwarded_to_hueify() -> None:
    hue = make_hue()

    await HueLights(hue).set_brightness(ROOM_ID, 80.5)

    hue.rooms.set_brightness.assert_awaited_once_with(ROOM_ID, 80.5)
