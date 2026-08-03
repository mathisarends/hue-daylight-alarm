from datetime import datetime, timezone
from uuid import UUID, uuid4

from huerise.features.alarm.domain.exceptions import AlarmAlreadyInStateError
from huerise.features.alarm.domain.views import Schedule


class Alarm:
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
        self.id = id if id is not None else uuid4()
        self.label = label
        self.schedule = schedule
        self.profile_id = profile_id
        self.room_name = room_name
        self.is_enabled = is_enabled
        self.created_at = (
            created_at if created_at is not None else datetime.now(timezone.utc)
        )

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
        return self.schedule.next_occurrence(after or datetime.now(timezone.utc))
