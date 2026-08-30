import asyncio
from uuid import UUID

import pytest

from huerise.configuration import DaylightAlarmConfig, HueriseConfig
from huerise.features.daylight_alarm.application import (
    AlarmAlreadyRunningError,
    DaylightAlarm,
)
from huerise.features.lighting.application import Room, Scene, SceneNotFoundError
from tests.huerise.fakes import FakeConfiguration
from tests.huerise.features.lighting.fakes import (
    FakeHueClient,
    FakeHueClientFactory,
    FakeHueCredentialsSource,
)

SCENE_ID = UUID(int=1)
ROOM_ID = UUID(int=2)


DEFAULT_ROOMS = [Room(ROOM_ID, "Bedroom", (Scene(SCENE_ID, "Sunrise"),))]


def make_alarm(
    client: FakeHueClient, *, duration: int = 2, sleep=asyncio.sleep
) -> DaylightAlarm:
    config = HueriseConfig(
        daylight_alarm=DaylightAlarmConfig(
            scene_id=SCENE_ID,
            start_brightness=10,
            end_brightness=30,
            duration_seconds=duration,
        )
    )
    return DaylightAlarm(
        FakeConfiguration(config),
        FakeHueCredentialsSource(),
        FakeHueClientFactory(client),
        step_interval=1,
        sleep=sleep,
    )


async def immediate_sleep(_: float) -> None:
    await asyncio.sleep(0)


async def test_runs_the_configured_ramp() -> None:
    client = FakeHueClient(DEFAULT_ROOMS)
    alarm = make_alarm(client, sleep=immediate_sleep)

    await alarm.start()
    assert alarm._task is not None
    await alarm._task

    assert client.commands == [
        ("activate", SCENE_ID, 10),
        ("brightness", ROOM_ID, 20),
        ("brightness", ROOM_ID, 30),
    ]
    assert client.closed is True
    assert alarm.is_running is False


async def test_stop_leaves_the_light_at_its_current_brightness() -> None:
    first_step = asyncio.Event()
    continue_sleep = asyncio.Event()

    async def controlled_sleep(_: float) -> None:
        if not first_step.is_set():
            first_step.set()
            return
        await continue_sleep.wait()

    client = FakeHueClient(DEFAULT_ROOMS)
    alarm = make_alarm(client, duration=3, sleep=controlled_sleep)
    await alarm.start()
    await first_step.wait()
    await asyncio.sleep(0)

    await alarm.stop()

    assert client.commands == [
        ("activate", SCENE_ID, 10),
        ("brightness", ROOM_ID, pytest.approx(16.67, abs=0.01)),
    ]
    assert client.closed is True
    assert alarm.is_running is False


async def test_rejects_a_second_start() -> None:
    never = asyncio.Event()

    async def blocked_sleep(_: float) -> None:
        await never.wait()

    alarm = make_alarm(FakeHueClient(DEFAULT_ROOMS), sleep=blocked_sleep)
    await alarm.start()

    with pytest.raises(AlarmAlreadyRunningError):
        await alarm.start()

    await alarm.stop()


async def test_stop_is_idempotent() -> None:
    alarm = make_alarm(FakeHueClient(DEFAULT_ROOMS))

    await alarm.stop()
    await alarm.stop()


async def test_start_fails_before_changing_light_when_scene_is_missing() -> None:
    client = FakeHueClient()
    alarm = make_alarm(client)

    with pytest.raises(SceneNotFoundError):
        await alarm.start()

    assert client.commands == []
    assert client.closed is True


async def test_overrides_only_the_duration_for_one_run() -> None:
    client = FakeHueClient(DEFAULT_ROOMS)
    alarm = make_alarm(client, duration=1800, sleep=immediate_sleep)

    duration = await alarm.start(duration_seconds=10)
    assert alarm._task is not None
    await alarm._task

    assert duration == 10
    assert client.commands[0] == ("activate", SCENE_ID, 10)
    assert client.commands[-1] == ("brightness", ROOM_ID, 30)
    assert len(client.commands) == 11
