from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from huerise.features.alarm.domain import (
    AlarmOccurrence,
    InvalidOccurrenceTransitionError,
    OccurrenceNotRunningError,
    OccurrenceState,
)

NOW = datetime(2026, 8, 3, 5, 0, tzinfo=timezone.utc)


def make_occurrence(
    state: OccurrenceState = OccurrenceState.PENDING,
) -> AlarmOccurrence:
    return AlarmOccurrence(alarm_id=uuid4(), scheduled_for=NOW, state=state)


class TestConstruction:
    def test_rejects_naive_scheduled_for(self) -> None:
        with pytest.raises(ValueError):
            AlarmOccurrence(alarm_id=uuid4(), scheduled_for=datetime(2026, 8, 3, 5, 0))

    def test_starts_pending(self) -> None:
        assert make_occurrence().state is OccurrenceState.PENDING


class TestLifecycle:
    def test_sunrise_records_the_trigger_time(self) -> None:
        occurrence = make_occurrence()

        occurrence.start_sunrise(NOW)

        assert occurrence.state is OccurrenceState.SUNRISE
        assert occurrence.triggered_at == NOW

    def test_ring_follows_sunrise(self) -> None:
        occurrence = make_occurrence(OccurrenceState.SUNRISE)

        occurrence.ring()

        assert occurrence.state is OccurrenceState.RINGING

    def test_ring_requires_sunrise(self) -> None:
        occurrence = make_occurrence(OccurrenceState.PENDING)

        with pytest.raises(InvalidOccurrenceTransitionError):
            occurrence.ring()

    def test_dismiss_finishes_the_run(self) -> None:
        occurrence = make_occurrence(OccurrenceState.RINGING)

        occurrence.dismiss(NOW)

        assert occurrence.state is OccurrenceState.DISMISSED
        assert occurrence.finished_at == NOW
        assert occurrence.is_finished

    def test_dismiss_is_rejected_once_finished(self) -> None:
        occurrence = make_occurrence(OccurrenceState.DISMISSED)

        with pytest.raises(InvalidOccurrenceTransitionError):
            occurrence.dismiss(NOW)

    def test_fail_records_the_reason(self) -> None:
        occurrence = make_occurrence(OccurrenceState.SUNRISE)

        occurrence.fail("bridge unreachable", NOW)

        assert occurrence.state is OccurrenceState.FAILED
        assert occurrence.failure_reason == "bridge unreachable"


class TestSnooze:
    def test_moves_the_scheduled_time_forward(self) -> None:
        occurrence = make_occurrence(OccurrenceState.RINGING)

        occurrence.snooze(minutes=9, now=NOW)

        assert occurrence.state is OccurrenceState.SNOOZED
        assert occurrence.scheduled_for == NOW + timedelta(minutes=9)
        assert occurrence.snooze_count == 1

    def test_counts_repeated_snoozes(self) -> None:
        occurrence = make_occurrence(OccurrenceState.RINGING)

        occurrence.snooze(minutes=5, now=NOW)
        occurrence.start_sunrise(NOW)
        occurrence.snooze(minutes=5, now=NOW)

        assert occurrence.snooze_count == 2

    def test_requires_a_running_occurrence(self) -> None:
        occurrence = make_occurrence(OccurrenceState.PENDING)

        with pytest.raises(OccurrenceNotRunningError):
            occurrence.snooze(now=NOW)

    def test_snoozed_occurrence_becomes_due_again(self) -> None:
        occurrence = make_occurrence(OccurrenceState.RINGING)

        occurrence.snooze(minutes=10, now=NOW)

        assert occurrence.is_due(NOW) is False
        assert occurrence.is_due(NOW + timedelta(minutes=10)) is True


class TestSkip:
    def test_skips_a_waiting_occurrence(self) -> None:
        occurrence = make_occurrence(OccurrenceState.PENDING)

        occurrence.skip(NOW)

        assert occurrence.state is OccurrenceState.SKIPPED
        assert occurrence.is_finished

    def test_cannot_skip_a_running_occurrence(self) -> None:
        occurrence = make_occurrence(OccurrenceState.RINGING)

        with pytest.raises(InvalidOccurrenceTransitionError):
            occurrence.skip(NOW)
