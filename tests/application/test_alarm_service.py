from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from huerise.features.alarm.domain import (
    AlarmNotFoundError,
    AlarmProfileNotFoundError,
    NoActiveOccurrenceError,
    OccurrenceState,
    Schedule,
    Weekday,
)
from tests.application.conftest import (
    InMemoryAlarmRepository,
    InMemoryOccurrenceRepository,
    InMemoryProfileRepository,
    make_alarm,
    make_alarm_service,
    make_audio,
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
            label="Work", schedule=Schedule(hour=6, minute=45), room_name="Bedroom"
        )

        assert alarm.profile_id == profile.id

    async def test_stores_weekdays_and_timezone(self) -> None:
        service = make_alarm_service()

        alarm = await service.create(
            label="Work",
            schedule=Schedule(
                hour=6, minute=45, weekdays=frozenset({Weekday.MON, Weekday.FRI})
            ),
            room_name="Bedroom",
        )

        assert alarm.schedule.weekdays == frozenset({Weekday.MON, Weekday.FRI})
        assert alarm.schedule.tz_name == "Europe/Berlin"

    async def test_without_weekdays_the_alarm_is_one_time(self) -> None:
        service = make_alarm_service()

        alarm = await service.create(
            label="Nap", schedule=Schedule(hour=14, minute=0), room_name="Bedroom"
        )

        assert alarm.schedule.is_recurring is False

    async def test_raises_when_no_profile_exists(self) -> None:
        service = make_alarm_service(profiles=InMemoryProfileRepository([]))

        with pytest.raises(AlarmProfileNotFoundError):
            await service.create(
                label="Work",
                schedule=Schedule(hour=6, minute=45),
                room_name="Bedroom",
            )

    async def test_raises_for_an_unknown_profile_id(self) -> None:
        service = make_alarm_service()

        with pytest.raises(AlarmProfileNotFoundError):
            await service.create(
                label="Work",
                schedule=Schedule(hour=6, minute=45),
                room_name="Bedroom",
                profile_id=uuid4(),
            )


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
        occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.RINGING)
        occurrences = InMemoryOccurrenceRepository([occurrence])
        audio = make_audio()
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=occurrences,
            audio=audio,
        )

        await service.disable(alarm.id)

        assert occurrences.items[occurrence.id].state is OccurrenceState.DISMISSED
        audio.stop.assert_awaited_once()

    async def test_raises_when_alarm_is_unknown(self) -> None:
        service = make_alarm_service()

        with pytest.raises(AlarmNotFoundError):
            await service.enable(uuid4())


class TestSnooze:
    async def test_moves_the_active_occurrence(self) -> None:
        alarm = make_alarm()
        occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.RINGING)
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
        )

        result = await service.snooze(alarm.id, minutes=10)

        assert result.state is OccurrenceState.SNOOZED
        assert result.scheduled_for > NOW + timedelta(minutes=9)

    async def test_stops_the_audio(self) -> None:
        alarm = make_alarm()
        occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.RINGING)
        audio = make_audio()
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
            audio=audio,
        )

        await service.snooze(alarm.id)

        audio.stop.assert_awaited_once()

    async def test_raises_without_an_active_occurrence(self) -> None:
        alarm = make_alarm()
        service = make_alarm_service(alarms=InMemoryAlarmRepository([alarm]))

        with pytest.raises(NoActiveOccurrenceError):
            await service.snooze(alarm.id)


class TestDismiss:
    async def test_finishes_the_active_occurrence(self) -> None:
        alarm = make_alarm()
        occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.RINGING)
        service = make_alarm_service(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
        )

        result = await service.dismiss(alarm.id)

        assert result.state is OccurrenceState.DISMISSED


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
