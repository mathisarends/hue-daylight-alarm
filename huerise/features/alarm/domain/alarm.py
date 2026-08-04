from datetime import UTC, datetime
from uuid import UUID

from huerise.features.alarm.domain.exceptions import AlarmAlreadyInStateError
from huerise.features.alarm.domain.views import AlarmField, Schedule
from huerise.shared.ddd import Aggregate


class Alarm(Aggregate):
    """The wake-up rule. Carries no runtime state -- that lives on occurrences."""

    def __init__(
        self,
        label: str,
        schedule: Schedule,
        profile_id: UUID,
        room_id: UUID,
        room_name: str,
        is_enabled: bool = True,
        id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(id, created_at)
        self.label = label
        self.schedule = schedule
        self.profile_id = profile_id
        self.room_id = room_id
        self.room_name = room_name
        self.is_enabled = is_enabled

    def update(
        self,
        label: str | None = None,
        schedule: Schedule | None = None,
        room_id: UUID | None = None,
        room_name: str | None = None,
        profile_id: UUID | None = None,
    ) -> list[AlarmField]:
        """Apply the fields that were given, naming the ones that really moved.

        None means "leave alone" -- none of these fields is nullable, so no
        separate sentinel is needed. The returned fields drive change
        notification, so a value re-sent unchanged must not appear.
        """
        changed: list[AlarmField] = []

        if label is not None and label != self.label:
            self.label = label
            changed.append(AlarmField.LABEL)
        if schedule is not None and schedule != self.schedule:
            self.schedule = schedule
            changed.append(AlarmField.SCHEDULE)
        if room_id is not None and room_id != self.room_id:
            self.room_id = room_id
            changed.append(AlarmField.ROOM)
        if room_name is not None and room_name != self.room_name:
            self.room_name = room_name
            if AlarmField.ROOM not in changed:
                changed.append(AlarmField.ROOM)
        if profile_id is not None and profile_id != self.profile_id:
            self.profile_id = profile_id
            changed.append(AlarmField.PROFILE_ID)

        return changed

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
