from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from huerise.features.alarm.application import LightReferenceSync
from huerise.features.alarm.domain import Alarm, AlarmDefect, AlarmField, AlarmProfile
from huerise.features.devices.application import LightEvents, Lights
from huerise.features.devices.domain import LightChange, LightResource, Room, Scene
from huerise.features.events.domain import AlarmUpdated, ProfileUpdated
from tests.application.conftest import (
    ROOM_ID,
    SCENE_ID,
    FakeUnitOfWork,
    FakeUnitOfWorkFactory,
    InMemoryAlarmRepository,
    InMemoryOccurrenceRepository,
    InMemoryProfileRepository,
    RecordingPublisher,
    make_alarm,
    make_profile,
)

OTHER_ROOM_ID = UUID("33333333-3333-4333-8333-333333333333")
OTHER_SCENE_ID = UUID("44444444-4444-4444-8444-444444444444")


def bedroom(*scenes: Scene, id: UUID = ROOM_ID, name: str = "Bedroom") -> Room:
    return Room(id=id, name=name, scenes=scenes)


def sunrise_scene(
    id: UUID = SCENE_ID, name: str = "Tageslichtwecker", brightness: float | None = 72
) -> Scene:
    return Scene(id=id, name=name, brightness=brightness)


def room_change(id: UUID = ROOM_ID, name: str | None = None) -> LightChange:
    return LightChange(resource=LightResource.ROOM, id=id, name=name)


def scene_change(id: UUID = SCENE_ID, name: str | None = None) -> LightChange:
    return LightChange(resource=LightResource.SCENE, id=id, name=name)


class Harness:
    """One sync wired to in-memory repositories and a recording stream."""

    def __init__(
        self, alarms: list[Alarm], profiles: list[AlarmProfile], rooms: list[Room]
    ) -> None:
        self.alarms = InMemoryAlarmRepository(alarms)
        self.profiles = InMemoryProfileRepository(profiles)
        self.events = MagicMock(spec=LightEvents)
        self.lights = MagicMock(spec=Lights)
        self.lights.list_rooms = AsyncMock(return_value=rooms)
        self.published = RecordingPublisher()
        self.sync = LightReferenceSync(
            events=self.events,
            lights=self.lights,
            unit_of_work_factory=FakeUnitOfWorkFactory(
                FakeUnitOfWork(
                    self.alarms, self.profiles, InMemoryOccurrenceRepository()
                )
            ),
            publisher=self.published,
        )

    async def receive(self, change: LightChange) -> None:
        await self.sync._on_change(change)

    def alarm(self, alarm: Alarm) -> Alarm:
        stored = self.alarms.items[alarm.id]
        assert stored is not None
        return stored

    def profile(self, profile: AlarmProfile) -> AlarmProfile:
        return self.profiles.items[profile.id]


@pytest.fixture
def paired() -> tuple[AlarmProfile, Alarm]:
    """A profile and the alarm that runs it, pointing at the bedroom scene."""
    profile = make_profile()
    return profile, make_alarm(profile_id=profile.id)


async def test_subscription_is_owned_by_its_lifecycle() -> None:
    harness = Harness([], [], [])

    await harness.sync.start()
    harness.events.subscribe.assert_called_once_with(harness.sync._on_change)

    await harness.sync.stop()
    harness.events.unsubscribe.assert_called_once_with(harness.sync._on_change)


class TestRoom:
    async def test_a_rename_reaches_every_alarm_in_that_room(self) -> None:
        alarm = make_alarm()
        harness = Harness([alarm], [], [bedroom(name="Schlafzimmer")])

        await harness.receive(room_change(name="Schlafzimmer"))

        assert harness.alarm(alarm).room_name == "Schlafzimmer"
        published = harness.published.only(AlarmUpdated)
        assert published.changed == [AlarmField.ROOM]
        assert published.alarm.room_name == "Schlafzimmer"

    async def test_a_name_that_did_not_move_is_not_reported(self) -> None:
        harness = Harness([make_alarm()], [], [bedroom()])

        await harness.receive(room_change(name="Bedroom"))

        assert harness.published.events == []

    async def test_a_room_nothing_points_at_is_never_looked_up(self) -> None:
        harness = Harness([make_alarm()], [], [bedroom()])

        await harness.receive(room_change(id=OTHER_ROOM_ID))

        harness.lights.list_rooms.assert_not_awaited()
        assert harness.published.events == []

    async def test_an_update_that_is_not_a_deletion_changes_nothing(self) -> None:
        harness = Harness([make_alarm()], [], [bedroom()])

        await harness.receive(room_change())

        harness.lights.list_rooms.assert_awaited_once()
        assert harness.published.events == []

    async def test_a_room_rebuilt_under_a_new_id_is_adopted(self) -> None:
        alarm = make_alarm()
        alarm.set_defect(AlarmDefect.ROOM_MISSING)
        harness = Harness([alarm], [], [bedroom(id=OTHER_ROOM_ID)])

        await harness.receive(room_change())

        stored = harness.alarm(alarm)
        assert stored.room_id == OTHER_ROOM_ID
        assert stored.defect is None
        published = harness.published.only(AlarmUpdated)
        assert published.changed == [AlarmField.ROOM, AlarmField.DEFECT]

    async def test_a_room_without_a_namesake_breaks_its_alarms(self) -> None:
        alarm = make_alarm()
        harness = Harness([alarm], [], [bedroom(id=OTHER_ROOM_ID, name="Kitchen")])

        await harness.receive(room_change())

        assert harness.alarm(alarm).defect is AlarmDefect.ROOM_MISSING
        published = harness.published.only(AlarmUpdated)
        assert published.changed == [AlarmField.DEFECT]
        assert published.alarm.defect is AlarmDefect.ROOM_MISSING

    async def test_a_defect_is_reported_once(self) -> None:
        alarm = make_alarm()
        alarm.set_defect(AlarmDefect.ROOM_MISSING)
        harness = Harness([alarm], [], [])

        await harness.receive(room_change())

        assert harness.published.events == []

    async def test_a_room_that_reappears_clears_the_defect(self) -> None:
        alarm = make_alarm()
        alarm.set_defect(AlarmDefect.ROOM_MISSING)
        harness = Harness([alarm], [], [bedroom()])

        await harness.receive(room_change(name="Bedroom"))

        assert harness.alarm(alarm).defect is None
        assert harness.published.only(AlarmUpdated).changed == [AlarmField.DEFECT]


class TestScene:
    async def test_a_rename_reaches_the_profile(
        self, paired: tuple[AlarmProfile, Alarm]
    ) -> None:
        profile, alarm = paired
        harness = Harness([alarm], [profile], [bedroom(sunrise_scene(name="Sonne"))])

        await harness.receive(scene_change(name="Sonne"))

        assert harness.profile(profile).sunrise_config.scene_name == "Sonne"
        published = harness.published.only(ProfileUpdated)
        assert published.profile.sunrise.scene_name == "Sonne"
        assert published.profile.sunrise.scene_id == SCENE_ID

    async def test_a_scene_no_profile_points_at_is_never_looked_up(
        self, paired: tuple[AlarmProfile, Alarm]
    ) -> None:
        profile, alarm = paired
        harness = Harness([alarm], [profile], [bedroom(sunrise_scene())])

        await harness.receive(scene_change(id=OTHER_SCENE_ID))

        harness.lights.list_rooms.assert_not_awaited()
        assert harness.published.events == []

    async def test_a_recall_of_a_living_scene_changes_nothing(
        self, paired: tuple[AlarmProfile, Alarm]
    ) -> None:
        profile, alarm = paired
        harness = Harness([alarm], [profile], [bedroom(sunrise_scene())])

        await harness.receive(scene_change())

        harness.lights.list_rooms.assert_awaited_once()
        assert harness.published.events == []

    async def test_a_scene_rebuilt_under_a_new_id_is_adopted(
        self, paired: tuple[AlarmProfile, Alarm]
    ) -> None:
        profile, alarm = paired
        rebuilt = sunrise_scene(id=OTHER_SCENE_ID)
        harness = Harness([alarm], [profile], [bedroom(rebuilt)])

        await harness.receive(scene_change())

        assert harness.profile(profile).sunrise_config.scene_id == OTHER_SCENE_ID
        assert harness.published.only(ProfileUpdated).profile.sunrise.scene_id == (
            OTHER_SCENE_ID
        )

    async def test_a_scene_without_a_namesake_falls_back_to_the_brightest(
        self, paired: tuple[AlarmProfile, Alarm]
    ) -> None:
        profile, alarm = paired
        harness = Harness(
            [alarm],
            [profile],
            [
                bedroom(
                    sunrise_scene(id=uuid4(), name="Nightlight", brightness=1),
                    sunrise_scene(id=uuid4(), name="Relax", brightness=40),
                    sunrise_scene(id=OTHER_SCENE_ID, name="Bright", brightness=90),
                )
            ],
        )

        await harness.receive(scene_change())

        sunrise = harness.profile(profile).sunrise_config
        assert sunrise.scene_id == OTHER_SCENE_ID
        assert sunrise.scene_name == "Bright"
        assert harness.alarm(alarm).defect is None

    async def test_a_namesake_beats_a_brighter_scene(
        self, paired: tuple[AlarmProfile, Alarm]
    ) -> None:
        profile, alarm = paired
        harness = Harness(
            [alarm],
            [profile],
            [
                bedroom(
                    sunrise_scene(id=OTHER_SCENE_ID, brightness=30),
                    sunrise_scene(id=uuid4(), name="Bright", brightness=90),
                )
            ],
        )

        await harness.receive(scene_change())

        assert harness.profile(profile).sunrise_config.scene_id == OTHER_SCENE_ID

    async def test_scenes_too_dim_to_ramp_to_are_no_replacement(
        self, paired: tuple[AlarmProfile, Alarm]
    ) -> None:
        profile, alarm = paired
        harness = Harness(
            [alarm],
            [profile],
            [bedroom(sunrise_scene(id=uuid4(), name="Nightlight", brightness=1))],
        )

        await harness.receive(scene_change())

        assert harness.profile(profile).sunrise_config.scene_id == SCENE_ID
        assert harness.alarm(alarm).defect is AlarmDefect.SCENE_MISSING
        assert harness.published.only(AlarmUpdated).changed == [AlarmField.DEFECT]

    async def test_scenes_of_another_room_are_no_replacement(
        self, paired: tuple[AlarmProfile, Alarm]
    ) -> None:
        profile, alarm = paired
        harness = Harness(
            [alarm],
            [profile],
            [
                bedroom(),
                bedroom(
                    sunrise_scene(id=uuid4(), name="Bright", brightness=90),
                    id=OTHER_ROOM_ID,
                    name="Kitchen",
                ),
            ],
        )

        await harness.receive(scene_change())

        assert harness.alarm(alarm).defect is AlarmDefect.SCENE_MISSING

    async def test_a_missing_room_outranks_a_missing_scene(
        self, paired: tuple[AlarmProfile, Alarm]
    ) -> None:
        profile, alarm = paired
        alarm.set_defect(AlarmDefect.ROOM_MISSING)
        harness = Harness([alarm], [profile], [])

        await harness.receive(scene_change())

        assert harness.alarm(alarm).defect is AlarmDefect.ROOM_MISSING
        assert harness.published.events == []

    async def test_a_scene_that_reappears_clears_the_defect(
        self, paired: tuple[AlarmProfile, Alarm]
    ) -> None:
        profile, alarm = paired
        alarm.set_defect(AlarmDefect.SCENE_MISSING)
        harness = Harness([alarm], [profile], [bedroom(sunrise_scene())])

        await harness.receive(scene_change(name="Tageslichtwecker"))

        assert harness.alarm(alarm).defect is None
        assert harness.published.only(AlarmUpdated).changed == [AlarmField.DEFECT]
