from dataclasses import dataclass
from uuid import UUID

import pytest

from huerise.configuration import DaylightAlarmConfig, HueriseConfig
from huerise.features.lighting.application import (
    Doctor,
    HueCredentials,
    HueUnavailableError,
    Room,
    Scene,
    SceneNotFoundError,
)

SCENE_ID = UUID(int=1)
ROOM_ID = UUID(int=2)


class StubConfiguration:
    def load(self) -> HueriseConfig:
        return HueriseConfig(
            daylight_alarm=DaylightAlarmConfig(
                scene_id=SCENE_ID,
                start_brightness=1,
                end_brightness=100,
                duration_seconds=1800,
            )
        )


class StubCredentials:
    def get(self) -> HueCredentials:
        return HueCredentials("192.0.2.10", "secret")


class StubClient:
    def __init__(self, rooms: list[Room]) -> None:
        self.rooms = rooms
        self.closed = False

    async def list_rooms(self) -> list[Room]:
        return self.rooms

    async def activate_scene(self, scene_id: UUID, *, brightness: float) -> None:
        raise AssertionError("doctor must not activate a scene")

    async def set_brightness(self, room_id: UUID, brightness: float) -> None:
        raise AssertionError("doctor must not change brightness")

    async def close(self) -> None:
        self.closed = True


@dataclass
class StubFactory:
    client: StubClient

    def create(self, _: HueCredentials) -> StubClient:
        return self.client


async def test_checks_configuration_bridge_and_scene_without_changing_lights() -> None:
    client = StubClient([Room(ROOM_ID, "Bedroom", (Scene(SCENE_ID, "Sunrise"),))])
    doctor = Doctor(StubConfiguration(), StubCredentials(), StubFactory(client))

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
    client = StubClient([])
    doctor = Doctor(StubConfiguration(), StubCredentials(), StubFactory(client))

    with pytest.raises(SceneNotFoundError):
        await doctor.check()

    assert client.closed is True


async def test_reports_bridge_failures() -> None:
    class BrokenClient(StubClient):
        async def list_rooms(self) -> list[Room]:
            raise OSError("offline")

    client = BrokenClient([])
    doctor = Doctor(StubConfiguration(), StubCredentials(), StubFactory(client))

    with pytest.raises(HueUnavailableError, match="authenticate"):
        await doctor.check()

    assert client.closed is True
