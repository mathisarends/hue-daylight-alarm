from datetime import UTC, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from huerise.features.alarm.domain import (
    Alarm,
    AlarmAlreadyInStateError,
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


class TestNextOccurrence:
    def test_resolves_the_schedule(self) -> None:
        alarm = make_alarm()

        assert alarm.next_occurrence(NOW) == datetime(
            2026, 8, 3, 5, 0, tzinfo=UTC
        )

    def test_returns_none_while_disabled(self) -> None:
        alarm = make_alarm(is_enabled=False)

        assert alarm.next_occurrence(NOW) is None
