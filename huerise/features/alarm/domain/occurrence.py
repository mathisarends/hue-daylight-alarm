from datetime import UTC, datetime
from uuid import UUID

from huerise.features.alarm.domain.exceptions import InvalidOccurrenceTransitionError
from huerise.features.alarm.domain.views import OccurrenceState
from huerise.shared.ddd import Entity

_WAITING_STATES = {OccurrenceState.PENDING}
_RUNNING_STATES = {OccurrenceState.SUNRISE}
_FINAL_STATES = {
    OccurrenceState.DISMISSED,
    OccurrenceState.SKIPPED,
    OccurrenceState.FAILED,
}


class AlarmOccurrence(Entity):
    """One concrete wake-up run of an alarm."""

    def __init__(
        self,
        alarm_id: UUID,
        scheduled_for: datetime,
        state: OccurrenceState = OccurrenceState.PENDING,
        triggered_at: datetime | None = None,
        finished_at: datetime | None = None,
        failure_reason: str | None = None,
        id: UUID | None = None,
    ) -> None:
        if scheduled_for.tzinfo is None:
            raise ValueError("scheduled_for must be timezone-aware")

        super().__init__(id)
        self.alarm_id = alarm_id
        self.scheduled_for = scheduled_for
        self.state = state
        self.triggered_at = triggered_at
        self.finished_at = finished_at
        self.failure_reason = failure_reason

    @property
    def is_waiting(self) -> bool:
        return self.state in _WAITING_STATES

    @property
    def is_running(self) -> bool:
        return self.state in _RUNNING_STATES

    @property
    def is_finished(self) -> bool:
        return self.state in _FINAL_STATES

    def is_due(self, now: datetime) -> bool:
        return self.is_waiting and self.scheduled_for <= now

    def start_sunrise(self, now: datetime | None = None) -> None:
        self._require(_WAITING_STATES, OccurrenceState.SUNRISE)
        self.state = OccurrenceState.SUNRISE
        self.triggered_at = now or datetime.now(UTC)

    def dismiss(self, now: datetime | None = None) -> None:
        self._require(_RUNNING_STATES | _WAITING_STATES, OccurrenceState.DISMISSED)
        self.state = OccurrenceState.DISMISSED
        self.finished_at = now or datetime.now(UTC)

    def skip(self, now: datetime | None = None) -> None:
        """Drop a run that is no longer worth firing, e.g. missed while offline."""
        self._require(_WAITING_STATES, OccurrenceState.SKIPPED)
        self.state = OccurrenceState.SKIPPED
        self.finished_at = now or datetime.now(UTC)

    def fail(self, reason: str, now: datetime | None = None) -> None:
        self.state = OccurrenceState.FAILED
        self.failure_reason = reason
        self.finished_at = now or datetime.now(UTC)

    def _require(self, allowed: set[OccurrenceState], target: OccurrenceState) -> None:
        if self.state not in allowed:
            raise InvalidOccurrenceTransitionError(self.id, self.state, target)
