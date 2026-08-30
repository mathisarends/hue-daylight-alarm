import asyncio
from dataclasses import dataclass
from uuid import UUID

import pytest

from huerise.configuration import DaylightAlarmConfig, HueriseConfig
from huerise.features.daylight_alarm.application import (
    AlarmAlreadyRunningError,
    DaylightAlarm,
)
from huerise.features.lighting.application import (
    HueCredentials,
    Room,
    Scene,
    SceneNotFoundError,
)

SCENE_ID = UUID(int=1)
ROOM_ID = UUID(int=2)


@dataclass
class StubConfiguration:
    config: HueriseConfig

    def load(self) -> HueriseConfig:
        return self.config


class StubCredentials:
    def get(self) -> HueCredentials:
        return HueCredentials("192.0.2.10", "secret")


class StubClient:
    def __init__(self, rooms: list[Room] | None = None) -> None:
        self.rooms = (
            rooms
            if rooms is not None
            else [Room(ROOM_ID, "Bedroom", (Scene(SCENE_ID, "Sunrise"),))]
        )
        self.commands: list[tuple] = []
        self.closed = False

    async def list_rooms(self) -> list[Room]:
        return self.rooms

    async def activate_scene(self, scene_id: UUID, *, brightness: float) -> None:
        self.commands.append(("activate", scene_id, brightness))

    async def set_brightness(self, room_id: UUID, brightness: float) -> None:
        self.commands.append(("brightness", room_id, brightness))

    async def close(self) -> None:
        self.closed = True


@dataclass
class StubFactory:
    client: StubClient

    def create(self, credentials: HueCredentials) -> StubClient:
        assert credentials.app_key == "secret"
        return self.client


def make_alarm(
    client: StubClient, *, duration: int = 2, sleep=asyncio.sleep
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
        StubConfiguration(config),
        StubCredentials(),
        StubFactory(client),
        step_interval=1,
        sleep=sleep,
    )


async def immediate_sleep(_: float) -> None:
    await asyncio.sleep(0)


async def test_runs_the_configured_ramp() -> None:
    client = StubClient()
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

    client = StubClient()
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

    alarm = make_alarm(StubClient(), sleep=blocked_sleep)
    await alarm.start()

    with pytest.raises(AlarmAlreadyRunningError):
        await alarm.start()

    await alarm.stop()


async def test_stop_is_idempotent() -> None:
    alarm = make_alarm(StubClient())

    await alarm.stop()
    await alarm.stop()


async def test_start_fails_before_changing_light_when_scene_is_missing() -> None:
    client = StubClient(rooms=[])
    alarm = make_alarm(client)

    with pytest.raises(SceneNotFoundError):
        await alarm.start()

    assert client.commands == []
    assert client.closed is True


async def test_overrides_only_the_duration_for_one_run() -> None:
    client = StubClient()
    alarm = make_alarm(client, duration=1800, sleep=immediate_sleep)

    duration = await alarm.start(duration_seconds=10)
    assert alarm._task is not None
    await alarm._task

    assert duration == 10
    assert client.commands[0] == ("activate", SCENE_ID, 10)
    assert client.commands[-1] == ("brightness", ROOM_ID, 30)
    assert len(client.commands) == 11
