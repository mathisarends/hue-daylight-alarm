from uuid import UUID

import pytest

from huerise.configuration import DaylightAlarmConfig, HueriseConfig
from huerise.features.lighting.application import (
    Doctor,
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


CONFIG = HueriseConfig(
    daylight_alarm=DaylightAlarmConfig(
        scene_id=SCENE_ID,
        start_brightness=1,
        end_brightness=100,
        duration_seconds=1800,
    )
)


def make_doctor(client: FakeHueClient) -> Doctor:
    return Doctor(
        FakeConfiguration(CONFIG),
        FakeHueCredentialsSource(),
        FakeHueClientFactory(client),
    )


async def test_checks_configuration_bridge_and_scene_without_changing_lights() -> None:
    client = FakeHueClient([Room(ROOM_ID, "Bedroom", (Scene(SCENE_ID, "Sunrise"),))])
    doctor = make_doctor(client)

    report = await doctor.check()

    assert report.status == "ok"
    assert [check.name for check in report.checks] == [
        "configuration",
        "hue_credentials",
        "hue_bridge",
        "scene",
    ]
    assert client.closed is True


async def test_reports_a_missing_scene() -> None:
    client = FakeHueClient()
    doctor = make_doctor(client)

    with pytest.raises(SceneNotFoundError):
        await doctor.check()

    assert client.closed is True


async def test_reports_bridge_failures() -> None:
    client = FakeHueClient(list_rooms_error=OSError("offline"))
    doctor = make_doctor(client)

    with pytest.raises(HueUnavailableError, match="authenticate"):
        await doctor.check()

    assert client.closed is True


async def test_reports_client_initialization_failures() -> None:
    client = FakeHueClient()
    doctor = Doctor(
        FakeConfiguration(CONFIG),
        FakeHueCredentialsSource(),
        FakeHueClientFactory(client, error=OSError("invalid transport")),
    )

    with pytest.raises(HueUnavailableError, match="initialize Hue Bridge connection"):
        await doctor.check()

    assert client.closed is False
