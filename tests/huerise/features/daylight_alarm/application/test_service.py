import asyncio
import logging
from uuid import UUID

import pytest

from huerise.configuration import (
    AfterAlarmConfig,
    DaylightAlarmConfig,
    HueriseConfig,
    NamedResourceConfig,
)
from huerise.features.daylight_alarm.application import (
    AlarmAlreadyRunningError,
    DaylightAlarm,
)
from huerise.features.lighting.application import (
    HueUnavailableError,
    Room,
    Scene,
    SceneNotFoundError,
)
from tests.huerise.fakes import FakeConfiguration
from tests.huerise.features.lighting.fakes import (
    FakeHueClient,
    FakeHueClientFactory,
    FakeHueCredentialsSource,
)

SCENE_ID = UUID(int=1)
ROOM_ID = UUID(int=2)


DEFAULT_ROOMS = [Room(ROOM_ID, "Bedroom", (Scene(SCENE_ID, "Sunrise", 30),))]


def make_alarm(
    client: FakeHueClient, *, duration: int = 2, sleep=asyncio.sleep
) -> DaylightAlarm:
    config = HueriseConfig(
        daylight_alarm=DaylightAlarmConfig(
            room=NamedResourceConfig(id=ROOM_ID, name="Bedroom"),
            scene=NamedResourceConfig(id=SCENE_ID, name="Sunrise"),
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


async def test_runs_from_one_percent_to_the_scenes_brightness() -> None:
    client = FakeHueClient(DEFAULT_ROOMS)
    alarm = make_alarm(client, sleep=immediate_sleep)

    await alarm.start()
    assert alarm._task is not None
    await alarm._task

    assert client.commands == [
        ("activate", SCENE_ID, 1),
        ("brightness", ROOM_ID, 15.5),
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
        ("activate", SCENE_ID, 1),
        ("brightness", ROOM_ID, pytest.approx(10.67, abs=0.01)),
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


async def test_start_fails_before_changing_light_when_scene_has_no_brightness() -> None:
    client = FakeHueClient([Room(ROOM_ID, "Bedroom", (Scene(SCENE_ID, "Sunrise"),))])
    alarm = make_alarm(client)

    with pytest.raises(HueUnavailableError, match="scene has no brightness"):
        await alarm.start()

    assert client.commands == []
    assert client.closed is True


async def test_start_fails_when_after_alarm_scene_has_no_brightness() -> None:
    after_alarm_scene_id = UUID(int=3)
    client = FakeHueClient(
        [
            Room(
                ROOM_ID,
                "Bedroom",
                (Scene(SCENE_ID, "Sunrise", 30), Scene(after_alarm_scene_id, "Dim")),
            )
        ]
    )
    config = HueriseConfig(
        daylight_alarm=DaylightAlarmConfig(
            room=NamedResourceConfig(id=ROOM_ID, name="Bedroom"),
            scene=NamedResourceConfig(id=SCENE_ID, name="Sunrise"),
            duration_seconds=2,
            after_alarm=AfterAlarmConfig(
                room=NamedResourceConfig(id=ROOM_ID, name="Bedroom"),
                scene=NamedResourceConfig(id=after_alarm_scene_id, name="Dim"),
                delay_seconds=60,
            ),
        )
    )
    alarm = DaylightAlarm(
        FakeConfiguration(config),
        FakeHueCredentialsSource(),
        FakeHueClientFactory(client),
        sleep=immediate_sleep,
    )

    with pytest.raises(HueUnavailableError, match="after-alarm Hue scene has no"):
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
    assert client.commands[0] == ("activate", SCENE_ID, 1)
    assert client.commands[-1] == ("brightness", ROOM_ID, 30)
    assert len(client.commands) == 11


async def test_activates_the_optional_after_alarm_scene() -> None:
    client = FakeHueClient(DEFAULT_ROOMS)
    config = HueriseConfig(
        daylight_alarm=DaylightAlarmConfig(
            room=NamedResourceConfig(id=ROOM_ID, name="Bedroom"),
            scene=NamedResourceConfig(id=SCENE_ID, name="Sunrise"),
            duration_seconds=2,
            after_alarm=AfterAlarmConfig(
                room=NamedResourceConfig(id=ROOM_ID, name="Bedroom"),
                scene=NamedResourceConfig(id=SCENE_ID, name="Sunrise"),
                delay_seconds=60,
            ),
        )
    )
    alarm = DaylightAlarm(
        FakeConfiguration(config),
        FakeHueCredentialsSource(),
        FakeHueClientFactory(client),
        sleep=immediate_sleep,
    )

    await alarm.start()
    assert alarm._task is not None
    await alarm._task

    assert client.commands[-1] == ("activate", SCENE_ID, 30)


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (HueUnavailableError("not configured"), "not configured"),
        (OSError("connection failed"), "initialize Hue Bridge connection"),
    ],
)
async def test_reports_client_initialization_failures(
    error: Exception, message: str
) -> None:
    client = FakeHueClient(DEFAULT_ROOMS)
    factory = FakeHueClientFactory(client, error=error)
    alarm = DaylightAlarm(
        FakeConfiguration(
            HueriseConfig(
                daylight_alarm=DaylightAlarmConfig(
                    room=NamedResourceConfig(id=ROOM_ID, name="Bedroom"),
                    scene=NamedResourceConfig(id=SCENE_ID, name="Sunrise"),
                    duration_seconds=2,
                )
            )
        ),
        FakeHueCredentialsSource(),
        factory,
    )

    with pytest.raises(HueUnavailableError, match=message):
        await alarm.start()

    assert client.commands == []
    assert client.closed is False


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (HueUnavailableError("offline"), "offline"),
        (OSError("protocol error"), "communicate with Hue Bridge"),
    ],
)
async def test_reports_startup_communication_failures(
    error: Exception, message: str
) -> None:
    client = FakeHueClient(DEFAULT_ROOMS, activate_scene_error=error)
    alarm = make_alarm(client)

    with pytest.raises(HueUnavailableError, match=message):
        await alarm.start()

    assert client.closed is True


async def test_logs_runtime_and_cleanup_failures(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = FakeHueClient(
        DEFAULT_ROOMS,
        set_brightness_error=OSError("light disconnected"),
        close_error=OSError("socket stuck"),
    )
    alarm = make_alarm(client, sleep=immediate_sleep)

    with caplog.at_level(logging.WARNING):
        await alarm.start()
        assert alarm._task is not None
        await alarm._task

    assert "Daylight alarm failed during execution" in caplog.text
    assert "Could not close Hue client" in caplog.text
    assert client.closed is True
