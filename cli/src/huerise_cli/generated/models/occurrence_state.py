from enum import Enum


class OccurrenceState(str, Enum):
    DISMISSED = "dismissed"
    FAILED = "failed"
    PENDING = "pending"
    RINGING = "ringing"
    SKIPPED = "skipped"
    SNOOZED = "snoozed"
    SUNRISE = "sunrise"

    def __str__(self) -> str:
        return str(self.value)
