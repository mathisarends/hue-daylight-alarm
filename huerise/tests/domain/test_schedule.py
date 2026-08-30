from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from huerise.features.alarm.domain import Schedule, Weekday

BERLIN = ZoneInfo("Europe/Berlin")


def utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=UTC)


def local(*args: int) -> datetime:
    return datetime(*args, tzinfo=BERLIN)


class TestNextOccurrenceOneTime:
    def test_returns_today_when_time_is_still_ahead(self) -> None:
        schedule = Schedule(hour=7, minute=0, tz=BERLIN)

        # 2026-08-03 04:00 UTC == 06:00 Berlin
        assert schedule.next_occurrence(utc(2026, 8, 3, 4, 0)) == utc(2026, 8, 3, 5, 0)

    def test_rolls_over_to_tomorrow_when_time_has_passed(self) -> None:
        schedule = Schedule(hour=7, minute=0, tz=BERLIN)

        assert schedule.next_occurrence(utc(2026, 8, 3, 6, 0)) == utc(2026, 8, 4, 5, 0)

    def test_is_strictly_after_the_reference_instant(self) -> None:
        schedule = Schedule(hour=7, minute=0, tz=BERLIN)

        assert schedule.next_occurrence(utc(2026, 8, 3, 5, 0)) == utc(2026, 8, 4, 5, 0)

    def test_rejects_naive_reference(self) -> None:
        schedule = Schedule(hour=7, minute=0, tz=BERLIN)

        with pytest.raises(ValueError):
            schedule.next_occurrence(datetime(2026, 8, 3, 5, 0))


class TestNextOccurrenceRecurring:
    def test_picks_the_next_matching_weekday(self) -> None:
        # 2026-08-03 is a Monday
        schedule = Schedule(
            hour=7, minute=0, tz=BERLIN, weekdays=frozenset({Weekday.WED})
        )

        assert schedule.next_occurrence(utc(2026, 8, 3, 4, 0)) == utc(2026, 8, 5, 5, 0)

    def test_wraps_into_the_following_week(self) -> None:
        schedule = Schedule(
            hour=7, minute=0, tz=BERLIN, weekdays=frozenset({Weekday.MON})
        )

        assert schedule.next_occurrence(utc(2026, 8, 3, 6, 0)) == utc(2026, 8, 10, 5, 0)

    def test_uses_the_earliest_of_several_days(self) -> None:
        schedule = Schedule(
            hour=7,
            minute=0,
            tz=BERLIN,
            weekdays=frozenset({Weekday.MON, Weekday.WED, Weekday.FRI}),
        )

        assert schedule.next_occurrence(utc(2026, 8, 3, 6, 0)) == utc(2026, 8, 5, 5, 0)


class TestDaylightSavingTime:
    def test_keeps_wall_clock_time_across_the_spring_transition(self) -> None:
        """07:00 Berlin stays 07:00 -- the UTC offset shifts, not the alarm."""
        schedule = Schedule(hour=7, minute=0, tz=BERLIN)

        # The switch happens at 02:00 on 2026-03-29, before either alarm time.
        before = schedule.next_occurrence(utc(2026, 3, 27, 12, 0))  # CET, +1
        after = schedule.next_occurrence(utc(2026, 3, 29, 12, 0))  # CEST, +2

        assert before == utc(2026, 3, 28, 6, 0)
        assert after == utc(2026, 3, 30, 5, 0)
        assert before.astimezone(BERLIN).hour == after.astimezone(BERLIN).hour == 7

    def test_keeps_wall_clock_time_across_the_autumn_transition(self) -> None:
        schedule = Schedule(hour=7, minute=0, tz=BERLIN)

        before = schedule.next_occurrence(utc(2026, 10, 24, 12, 0))  # CEST, +2
        after = schedule.next_occurrence(utc(2026, 10, 25, 12, 0))  # CET, +1

        assert before.astimezone(BERLIN).hour == after.astimezone(BERLIN).hour == 7

    def test_nonexistent_local_time_fires_once_after_the_gap(self) -> None:
        """02:30 does not exist on 2026-03-29; the alarm still fires exactly once."""
        schedule = Schedule(hour=2, minute=30, tz=BERLIN)

        fired = schedule.next_occurrence(utc(2026, 3, 28, 12, 0))

        assert fired == utc(2026, 3, 29, 1, 30)
        assert fired.astimezone(BERLIN) == local(2026, 3, 29, 3, 30)

    def test_ambiguous_local_time_fires_at_the_first_pass(self) -> None:
        """02:30 exists twice on 2026-10-25; only the earlier one is used."""
        schedule = Schedule(hour=2, minute=30, tz=BERLIN)

        fired = schedule.next_occurrence(utc(2026, 10, 24, 12, 0))

        assert fired == utc(2026, 10, 25, 0, 30)

        # The second 02:30 is one hour later and must not produce another run.
        following = schedule.next_occurrence(fired)
        assert following > utc(2026, 10, 25, 1, 30)


class TestRecurrenceMask:
    def test_roundtrips_through_the_mask(self) -> None:
        weekdays = frozenset({Weekday.MON, Weekday.FRI, Weekday.SUN})
        schedule = Schedule(hour=6, minute=45, tz=BERLIN, weekdays=weekdays)

        restored = Schedule.from_mask(
            hour=6, minute=45, tz=BERLIN, recurrence_mask=schedule.recurrence_mask
        )

        assert restored == schedule

    def test_empty_mask_means_one_time(self) -> None:
        schedule = Schedule.from_mask(hour=6, minute=45, tz=BERLIN, recurrence_mask=0)

        assert schedule.is_recurring is False
        assert schedule.recurrence_mask == 0


class TestValidation:
    @pytest.mark.parametrize("hour", [-1, 24])
    def test_rejects_hours_out_of_range(self, hour: int) -> None:
        with pytest.raises(ValueError):
            Schedule(hour=hour, minute=0)

    @pytest.mark.parametrize("minute", [-1, 60])
    def test_rejects_minutes_out_of_range(self, minute: int) -> None:
        with pytest.raises(ValueError):
            Schedule(hour=7, minute=minute)
