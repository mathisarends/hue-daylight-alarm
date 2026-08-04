from datetime import UTC, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from huerise.features.alarm.domain import (
    Alarm,
    AlarmAlreadyInStateError,
    AlarmField,
    Schedule,
    Weekday,
)

BERLIN = ZoneInfo("Europe/Berlin")
NOW = datetime(2026, 8, 3, 4, 0, tzinfo=UTC)


def make_alarm(is_enabled: bool = True, weekdays: frozenset[Weekday] = frozenset()):
    return Alarm(
        label="Morning",
        schedule=Schedule(hour=7, minute=0, tz=BERLIN, weekdays=weekdays),
        profile_id=uuid4(),
        room_name="Bedroom",
        is_enabled=is_enabled,
    )


class TestEnabling:
    def test_disable_stops_the_alarm(self) -> None:
        alarm = make_alarm()

        alarm.disable()

        assert alarm.is_enabled is False

    def test_disabling_twice_is_rejected(self) -> None:
        alarm = make_alarm(is_enabled=False)

        with pytest.raises(AlarmAlreadyInStateError):
            alarm.disable()

    def test_enabling_twice_is_rejected(self) -> None:
        alarm = make_alarm()

        with pytest.raises(AlarmAlreadyInStateError):
            alarm.enable()


class TestUpdate:
    def test_applies_the_fields_it_is_given(self) -> None:
        alarm = make_alarm()
        schedule = Schedule(hour=8, minute=30, tz=BERLIN)

        changed = alarm.update(label="Weekend", schedule=schedule)

        assert alarm.label == "Weekend"
        assert alarm.schedule == schedule
        assert changed == [AlarmField.LABEL, AlarmField.SCHEDULE]

    def test_leaves_omitted_fields_alone(self) -> None:
        alarm = make_alarm()

        alarm.update(label="Weekend")

        assert alarm.room_name == "Bedroom"
        assert alarm.schedule.hour == 7

    def test_reports_nothing_when_a_value_is_resent_unchanged(self) -> None:
        alarm = make_alarm()

        changed = alarm.update(
            label="Morning", schedule=Schedule(hour=7, minute=0, tz=BERLIN)
        )

        assert changed == []

    def test_reports_only_the_fields_that_moved(self) -> None:
        alarm = make_alarm()

        changed = alarm.update(label="Morning", room_name="Guest room")

        assert changed == [AlarmField.ROOM_NAME]


class TestNextOccurrence:
    def test_resolves_the_schedule(self) -> None:
        alarm = make_alarm()

        assert alarm.next_occurrence(NOW) == datetime(2026, 8, 3, 5, 0, tzinfo=UTC)

    def test_returns_none_while_disabled(self) -> None:
        alarm = make_alarm(is_enabled=False)

        assert alarm.next_occurrence(NOW) is None
