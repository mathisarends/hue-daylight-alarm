from uuid import UUID

from huerise.features.alarm.domain.views import OccurrenceState


class HueriseError(Exception):
    """Base for all domain exceptions."""


class AlarmNotFoundError(HueriseError):
    def __init__(self, alarm_id: UUID) -> None:
        super().__init__(f"Alarm {alarm_id} not found")


class AlarmProfileNotFoundError(HueriseError):
    def __init__(self, profile_id: UUID | None = None) -> None:
        target = str(profile_id) if profile_id is not None else "default"
        super().__init__(f"Alarm profile {target} not found")


class AlarmAlreadyInStateError(HueriseError):
    def __init__(self, alarm_id: UUID, enabled: bool) -> None:
        state = "enabled" if enabled else "disabled"
        super().__init__(f"Alarm {alarm_id} is already {state}")


class OccurrenceNotFoundError(HueriseError):
    def __init__(self, occurrence_id: UUID) -> None:
        super().__init__(f"Occurrence {occurrence_id} not found")


class NoActiveOccurrenceError(HueriseError):
    def __init__(self, alarm_id: UUID) -> None:
        super().__init__(f"Alarm {alarm_id} has no active occurrence")


class OccurrenceNotRunningError(HueriseError):
    def __init__(self, occurrence_id: UUID) -> None:
        super().__init__(f"Occurrence {occurrence_id} is not currently running")


class InvalidOccurrenceTransitionError(HueriseError):
    def __init__(
        self,
        occurrence_id: UUID,
        current: OccurrenceState,
        target: OccurrenceState,
    ) -> None:
        super().__init__(
            f"Occurrence {occurrence_id} cannot go from {current} to {target}"
        )
