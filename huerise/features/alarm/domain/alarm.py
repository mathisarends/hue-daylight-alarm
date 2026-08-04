from datetime import UTC, datetime
from uuid import UUID

from huerise.features.alarm.domain.exceptions import AlarmAlreadyInStateError
from huerise.features.alarm.domain.views import Schedule
from huerise.shared.ddd import Aggregate


class Alarm(Aggregate):
    """The wake-up rule. Carries no runtime state -- that lives on occurrences."""

    def __init__(
        self,
        label: str,
        schedule: Schedule,
        profile_id: UUID,
        room_name: str,
        is_enabled: bool = True,
        id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(id, created_at)
        self.label = label
        self.schedule = schedule
        self.profile_id = profile_id
        self.room_name = room_name
        self.is_enabled = is_enabled

    def enable(self) -> None:
        if self.is_enabled:
            raise AlarmAlreadyInStateError(self.id, enabled=True)
        self.is_enabled = True

    def disable(self) -> None:
        if not self.is_enabled:
            raise AlarmAlreadyInStateError(self.id, enabled=False)
        self.is_enabled = False

    def next_occurrence(self, after: datetime | None = None) -> datetime | None:
        """Next UTC instant this alarm fires, or None while disabled."""
        if not self.is_enabled:
            return None
        return self.schedule.next_occurrence(after or datetime.now(UTC))
