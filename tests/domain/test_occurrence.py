from datetime import UTC, datetime
from uuid import uuid4

import pytest

from huerise.features.alarm.domain import (
    AlarmOccurrence,
    InvalidOccurrenceTransitionError,
    OccurrenceState,
)

NOW = datetime(2026, 8, 3, 5, 0, tzinfo=UTC)


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

    def test_dismiss_finishes_the_run(self) -> None:
        occurrence = make_occurrence(OccurrenceState.SUNRISE)

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


class TestSkip:
    def test_skips_a_waiting_occurrence(self) -> None:
        occurrence = make_occurrence(OccurrenceState.PENDING)

        occurrence.skip(NOW)

        assert occurrence.state is OccurrenceState.SKIPPED
        assert occurrence.is_finished

    def test_cannot_skip_a_running_occurrence(self) -> None:
        occurrence = make_occurrence(OccurrenceState.SUNRISE)

        with pytest.raises(InvalidOccurrenceTransitionError):
            occurrence.skip(NOW)
