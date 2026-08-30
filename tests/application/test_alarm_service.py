from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from huerise.features.alarm.domain import (
    AlarmDefect,
    AlarmField,
    AlarmNotFoundError,
    AlarmProfileNotFoundError,
    NoActiveOccurrenceError,
    OccurrenceState,
    Schedule,
    Weekday,
)
from huerise.features.devices.domain import Room, SceneNotFoundError
from huerise.features.events.domain import (
    AlarmCreated,
    AlarmDeleted,
    AlarmUpdated,
    OccurrenceDismissed,
    OccurrenceSkipped,
)
from tests.application.conftest import (
    ROOM_ID,
    InMemoryAlarmRepository,
    InMemoryOccurrenceRepository,
    InMemoryProfileRepository,
    RecordingPublisher,
    make_alarm,
    make_alarm_service,
    make_lights,
    make_occurrence,
    make_profile,
)

NOW = datetime(2026, 8, 3, 5, 0, tzinfo=UTC)


class TestFindAlarm:
    async def test_returns_all_alarms(self) -> None:
        alarm = make_alarm()
        service = make_alarm_service(alarms=InMemoryAlarmRepository([alarm]))

        assert await service.find_all() == [alarm]

    async def test_returns_alarm_by_id(self) -> None:
        alarm = make_alarm()
        service = make_alarm_service(alarms=InMemoryAlarmRepository([alarm]))

        assert await service.find_by_id(alarm.id) == alarm

    async def test_raises_for_an_unknown_id(self) -> None:
        service = make_alarm_service()

        with pytest.raises(AlarmNotFoundError):
            await service.find_by_id(uuid4())


class TestCreateAlarm:
    async def test_uses_the_default_profile(self) -> None:
        profile = make_profile()
        service = make_alarm_service(profiles=InMemoryProfileRepository([profile]))

        alarm = await service.create(
            label="Work",
            schedule=Schedule(hour=6, minute=45),
            room_id=ROOM_ID,
            room_name="Bedroom",
        )

        assert alarm.profile_id == profile.id

    async def test_stores_weekdays_and_timezone(self) -> None:
        service = make_alarm_service()

        alarm = await service.create(
            label="Work",
            schedule=Schedule(
                hour=6, minute=45, weekdays=frozenset({Weekday.MON, Weekday.FRI})
            ),
            room_id=ROOM_ID,
            room_name="Bedroom",
        )

        assert alarm.schedule.weekdays == frozenset({Weekday.MON, Weekday.FRI})
        assert alarm.schedule.tz_name == "Europe/Berlin"

    async def test_without_weekdays_the_alarm_is_one_time(self) -> None:
        service = make_alarm_service()

        alarm = await service.create(
            label="Nap",
            schedule=Schedule(hour=14, minute=0),
            room_id=ROOM_ID,
            room_name="Bedroom",
        )

        assert alarm.schedule.is_recurring is False

    async def test_raises_when_no_profile_exists(self) -> None:
        service = make_alarm_service(profiles=InMemoryProfileRepository([]))

        with pytest.raises(AlarmProfileNotFoundError):
            await service.create(
                label="Work",
                schedule=Schedule(hour=6, minute=45),
                room_id=ROOM_ID,
                room_name="Bedroom",
            )

    async def test_raises_for_an_unknown_profile_id(self) -> None:
        service = make_alarm_service()

        with pytest.raises(AlarmProfileNotFoundError):
            await service.create(
                label="Work",
                schedule=Schedule(hour=6, minute=45),
                room_id=ROOM_ID,
                room_name="Bedroom",
                profile_id=uuid4(),
            )

    async def test_rejects_a_profile_scene_missing_from_the_hue_room(self) -> None:
        lights = make_lights()
        lights.list_rooms.return_value = [Room(id=ROOM_ID, name="Bedroom", scenes=())]
        alarms = InMemoryAlarmRepository()
        service = make_alarm_service(alarms=alarms, lights=lights)

        with pytest.raises(SceneNotFoundError):
            await service.create(
                label="Work",
                schedule=Schedule(hour=6, minute=45),
                room_id=ROOM_ID,
                room_name="Bedroom",
            )

        assert alarms.items == {}


class TestPublishedEvents:
    async def test_creating_announces_the_new_alarm(self) -> None:
        events = RecordingPublisher()
        service = make_alarm_service(events=events)

        alarm = await service.create(
            label="Work",
            schedule=Schedule(hour=6, minute=45),
            room_id=ROOM_ID,
            room_name="Bedroom",
        )

        assert events.only(AlarmCreated).alarm.id == alarm.id

    async def test_updating_names_the_fields_that_moved(self) -> None:
        alarm = make_alarm()
        events = RecordingPublisher()
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]), events=events
        )

        await service.update(alarm.id, label="Weekend")

        assert events.only(AlarmUpdated).changed == [AlarmField.LABEL]

    async def test_an_update_that_changes_nothing_stays_silent(self) -> None:
        alarm = make_alarm()
        events = RecordingPublisher()
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]), events=events
        )

        await service.update(alarm.id, label=alarm.label)

        assert events.events == []

    async def test_enabling_announces_the_flag_that_moved(self) -> None:
        alarm = make_alarm(is_enabled=False)
        events = RecordingPublisher()
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]), events=events
        )

        await service.enable(alarm.id)

        assert events.only(AlarmUpdated).changed == [AlarmField.IS_ENABLED]

    async def test_deleting_announces_the_id(self) -> None:
        alarm = make_alarm()
        events = RecordingPublisher()
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]), events=events
        )

        await service.delete(alarm.id)

        assert events.only(AlarmDeleted).alarm_id == alarm.id

    async def test_a_failed_delete_stays_silent(self) -> None:
        events = RecordingPublisher()
        service = make_alarm_service(events=events)

        with pytest.raises(AlarmNotFoundError):
            await service.delete(uuid4())

        assert events.events == []

    async def test_dismissing_announces_the_finished_run(self) -> None:
        alarm = make_alarm()
        occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.SUNRISE)
        events = RecordingPublisher()
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
            events=events,
        )

        await service.dismiss(alarm.id)

        assert events.only(OccurrenceDismissed).occurrence.state is (
            OccurrenceState.DISMISSED
        )

    async def test_rescheduling_announces_the_dropped_run(self) -> None:
        alarm = make_alarm(hour=7, minute=0)
        occurrence = make_occurrence(alarm.id, NOW)
        events = RecordingPublisher()
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
            events=events,
        )

        await service.update(alarm.id, schedule=Schedule(hour=9, minute=0))

        assert events.only(OccurrenceSkipped).occurrence.id == occurrence.id
        assert events.only(AlarmUpdated).changed == [AlarmField.SCHEDULE]

    async def test_disabling_a_ringing_alarm_announces_a_dismissal(self) -> None:
        alarm = make_alarm()
        occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.SUNRISE)
        events = RecordingPublisher()
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
            events=events,
        )

        await service.disable(alarm.id)

        assert events.only(OccurrenceDismissed).occurrence.id == occurrence.id

    async def test_disabling_a_waiting_alarm_announces_a_skip(self) -> None:
        alarm = make_alarm()
        occurrence = make_occurrence(alarm.id, NOW)
        events = RecordingPublisher()
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
            events=events,
        )

        await service.disable(alarm.id)

        assert events.only(OccurrenceSkipped).occurrence.id == occurrence.id


class TestUpdateAlarm:
    async def test_changes_only_what_was_sent(self) -> None:
        alarm = make_alarm(hour=7, minute=0)
        service = make_alarm_service(alarms=InMemoryAlarmRepository([alarm]))

        result = await service.update(alarm.id, label="Weekend")

        assert result.label == "Weekend"
        assert result.schedule.hour == 7

    async def test_raises_for_an_unknown_alarm(self) -> None:
        service = make_alarm_service()

        with pytest.raises(AlarmNotFoundError):
            await service.update(uuid4(), label="Weekend")

    async def test_rejects_an_unknown_profile_without_touching_the_alarm(self) -> None:
        alarm = make_alarm()
        service = make_alarm_service(alarms=InMemoryAlarmRepository([alarm]))

        with pytest.raises(AlarmProfileNotFoundError):
            await service.update(alarm.id, label="Weekend", profile_id=uuid4())

        assert alarm.label == "Morning"

    async def test_re_picking_the_room_clears_a_defect(self) -> None:
        """The room and scene were just checked, so the bridge trouble is over."""
        profile = make_profile()
        alarm = make_alarm(profile_id=profile.id)
        alarm.set_defect(AlarmDefect.ROOM_MISSING)
        published = RecordingPublisher()
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]),
            profiles=InMemoryProfileRepository([profile]),
            events=published,
        )

        result = await service.update(alarm.id, room_id=ROOM_ID, room_name="Bedroom")

        assert result.defect is None
        assert published.only(AlarmUpdated).changed == [AlarmField.DEFECT]

    async def test_rescheduling_skips_the_run_queued_for_the_old_time(self) -> None:
        alarm = make_alarm(hour=7, minute=0)
        occurrence = make_occurrence(alarm.id, NOW)
        occurrences = InMemoryOccurrenceRepository([occurrence])
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]), occurrences=occurrences
        )

        await service.update(alarm.id, schedule=Schedule(hour=9, minute=0))

        assert occurrence.state is OccurrenceState.SKIPPED

    async def test_a_change_other_than_the_time_keeps_the_queued_run(self) -> None:
        alarm = make_alarm()
        occurrence = make_occurrence(alarm.id, NOW)
        occurrences = InMemoryOccurrenceRepository([occurrence])
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]), occurrences=occurrences
        )

        await service.update(alarm.id, label="Weekend")

        assert occurrence.state is OccurrenceState.PENDING

    async def test_rescheduling_leaves_a_sunrise_already_running(self) -> None:
        alarm = make_alarm(hour=7, minute=0)
        occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.SUNRISE)
        occurrences = InMemoryOccurrenceRepository([occurrence])
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]), occurrences=occurrences
        )

        await service.update(alarm.id, schedule=Schedule(hour=9, minute=0))

        assert occurrence.state is OccurrenceState.SUNRISE


class TestEnableDisable:
    async def test_enable_reactivates_the_alarm(self) -> None:
        alarm = make_alarm(is_enabled=False)
        service = make_alarm_service(alarms=InMemoryAlarmRepository([alarm]))

        result = await service.enable(alarm.id)

        assert result.is_enabled is True

    async def test_disable_skips_a_pending_occurrence(self) -> None:
        alarm = make_alarm()
        occurrence = make_occurrence(alarm.id, NOW)
        occurrences = InMemoryOccurrenceRepository([occurrence])
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]), occurrences=occurrences
        )

        await service.disable(alarm.id)

        assert occurrences.items[occurrence.id].state is OccurrenceState.SKIPPED

    async def test_disable_dismisses_a_running_occurrence(self) -> None:
        alarm = make_alarm()
        occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.SUNRISE)
        occurrences = InMemoryOccurrenceRepository([occurrence])
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=occurrences,
        )

        await service.disable(alarm.id)

        assert occurrences.items[occurrence.id].state is OccurrenceState.DISMISSED

    async def test_disable_with_no_occurrences_is_a_noop(self) -> None:
        alarm = make_alarm()
        service = make_alarm_service(alarms=InMemoryAlarmRepository([alarm]))

        result = await service.disable(alarm.id)

        assert result.is_enabled is False

    async def test_raises_when_alarm_is_unknown(self) -> None:
        service = make_alarm_service()

        with pytest.raises(AlarmNotFoundError):
            await service.enable(uuid4())


class TestDismiss:
    async def test_finishes_the_active_occurrence(self) -> None:
        alarm = make_alarm()
        occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.SUNRISE)
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
        )

        result = await service.dismiss(alarm.id)

        assert result.state is OccurrenceState.DISMISSED

    async def test_raises_without_an_active_occurrence(self) -> None:
        alarm = make_alarm()
        service = make_alarm_service(alarms=InMemoryAlarmRepository([alarm]))

        with pytest.raises(NoActiveOccurrenceError):
            await service.dismiss(alarm.id)


class TestDelete:
    async def test_removes_the_alarm(self) -> None:
        alarm = make_alarm()
        alarms = InMemoryAlarmRepository([alarm])
        service = make_alarm_service(alarms=alarms)

        await service.delete(alarm.id)

        assert alarms.items == {}

    async def test_raises_for_an_unknown_alarm(self) -> None:
        service = make_alarm_service()

        with pytest.raises(AlarmNotFoundError):
            await service.delete(uuid4())


class TestListOccurrences:
    async def test_returns_newest_first(self) -> None:
        alarm = make_alarm()
        older = make_occurrence(alarm.id, NOW - timedelta(days=1))
        newer = make_occurrence(alarm.id, NOW)
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([older, newer]),
        )

        result = await service.list_occurrences(alarm.id)

        assert [o.id for o in result] == [newer.id, older.id]
