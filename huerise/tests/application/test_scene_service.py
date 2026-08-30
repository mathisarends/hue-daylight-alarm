import asyncio
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest

from huerise.features.lighting.application import (
    DEMO_STEP_INTERVAL,
    SceneService,
    SunriseDemoRunner,
)
from huerise.features.lighting.domain import (
    Room,
    RoomNotFoundError,
    Scene,
    SceneNotFoundError,
    SunriseRamp,
    sunrise_steps,
)
from huerise.tests.application.conftest import ROOM_ID, SCENE_ID, make_lights

RELAX_ID = SCENE_ID
BEDROOM = Room(
    id=ROOM_ID,
    name="Bedroom",
    scenes=(Scene(id=RELAX_ID, name="Relax"),),
)


def make_scene_service(
    step_interval: timedelta = DEMO_STEP_INTERVAL,
) -> tuple[SceneService, object]:
    lights = make_lights()
    lights.list_rooms.return_value = [BEDROOM]
    return SceneService(lights, SunriseDemoRunner(lights, step_interval)), lights


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


RAMP = SunriseRamp(duration=timedelta(seconds=20), brightness_start=10)

# Long enough that a demo blocks on its first sleep, so a test can interrupt it.
SLOW_STEP = timedelta(seconds=60)
SLOW_RAMP = SunriseRamp(duration=timedelta(minutes=5))

# Captured before `patch("asyncio.sleep")` can replace it: yielding to the
# background demo must keep working while its own sleeps are stubbed out.
_yield_to_demo = asyncio.sleep


async def drain() -> None:
    """Hand control to the background demo until it has run itself out."""
    for _ in range(3):
        await _yield_to_demo(0)


class TestSunriseDemo:
    async def test_reports_the_run_it_started(self) -> None:
        service, _ = make_scene_service()

        with patch("asyncio.sleep"):
            demo = await service.start_demo(ROOM_ID, RELAX_ID, RAMP)
            await drain()

        assert demo.room == BEDROOM
        assert demo.scene.name == "Relax"
        assert demo.ramp is RAMP
        assert demo.steps == 20
        assert demo.duration == timedelta(seconds=20)

    async def test_opens_on_the_scene_at_its_starting_brightness(self) -> None:
        service, lights = make_scene_service()

        with patch("asyncio.sleep"):
            await service.start_demo(ROOM_ID, RELAX_ID, RAMP)
            await drain()

        lights.activate_scene.assert_awaited_once_with(RELAX_ID, brightness=10)

    async def test_climbs_the_whole_ramp_in_the_background(self) -> None:
        service, lights = make_scene_service()

        with patch("asyncio.sleep"):
            await service.start_demo(ROOM_ID, RELAX_ID, RAMP)
            await drain()

        brightness = [call.args[1] for call in lights.set_brightness.await_args_list]
        assert brightness == [
            step.brightness for step in sunrise_steps(RAMP, DEMO_STEP_INTERVAL)
        ]

    async def test_rejects_a_scene_the_room_does_not_have(self) -> None:
        service, lights = make_scene_service()

        with pytest.raises(SceneNotFoundError):
            await service.start_demo(ROOM_ID, uuid4(), RAMP)

        lights.activate_scene.assert_not_awaited()

    async def test_stopping_leaves_the_lights_where_they_got_to(self) -> None:
        service, lights = make_scene_service(step_interval=SLOW_STEP)

        await service.start_demo(ROOM_ID, RELAX_ID, SLOW_RAMP)
        await drain()
        await service.stop_demo()

        assert lights.set_brightness.await_count == 1

    async def test_starting_a_second_demo_replaces_the_first(self) -> None:
        service, lights = make_scene_service(step_interval=SLOW_STEP)

        await service.start_demo(ROOM_ID, RELAX_ID, SLOW_RAMP)
        await drain()
        await service.start_demo(ROOM_ID, RELAX_ID, SLOW_RAMP)
        await drain()

        # One opening step each: the first demo was cut off, not left running.
        assert lights.activate_scene.await_count == 2
        assert lights.set_brightness.await_count == 2

    async def test_stopping_without_a_running_demo_is_harmless(self) -> None:
        service, _ = make_scene_service()

        await service.stop_demo()

    async def test_a_failing_bridge_ends_the_demo_without_escaping(self) -> None:
        service, lights = make_scene_service()
        lights.set_brightness.side_effect = OSError("bridge unreachable")

        with patch("asyncio.sleep"):
            await service.start_demo(ROOM_ID, RELAX_ID, RAMP)
            await drain()

        # The task swallowed it: nothing is left to fire an unretrieved-exception
        # warning, and a later demo still starts.
        lights.set_brightness.side_effect = None
        with patch("asyncio.sleep"):
            await service.start_demo(ROOM_ID, RELAX_ID, RAMP)
            await drain()
