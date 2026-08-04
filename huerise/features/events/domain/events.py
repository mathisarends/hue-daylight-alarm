from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, computed_field
from transitbus import Event

from huerise.features.alarm.domain import AlarmField
from huerise.features.events.domain.snapshots import AlarmSnapshot, OccurrenceSnapshot


class EventType(StrEnum):
    """The discriminator. Doubles as the SSE `event:` name a client listens on."""

    ALARM_CREATED = "alarm.created"
    ALARM_UPDATED = "alarm.updated"
    ALARM_DELETED = "alarm.deleted"
    NEXT_ALARM_CHANGED = "alarm.next_changed"

    OCCURRENCE_SCHEDULED = "occurrence.scheduled"
    OCCURRENCE_STARTED = "occurrence.started"
    OCCURRENCE_PROGRESS = "occurrence.progress"
    OCCURRENCE_RINGING = "occurrence.ringing"
    OCCURRENCE_SNOOZED = "occurrence.snoozed"
    OCCURRENCE_DISMISSED = "occurrence.dismissed"
    OCCURRENCE_SKIPPED = "occurrence.skipped"
    OCCURRENCE_FAILED = "occurrence.failed"


class HueriseEvent(Event):
    """Base for everything that goes out over the alarm event stream.

    A `transitbus.Event` is already a Pydantic model, so one class is both the
    in-process bus message and the SSE payload -- there is no mapping layer.
    Only `path` is bus bookkeeping and stays off the wire. `parent_id`
    deliberately does not: it tells a client which event caused this one.

    Subclasses narrow `type` to a single `Literal`, which both discriminates
    the union and names the SSE frame.
    """

    type: EventType
    path: list[str] = Field(default_factory=list, exclude=True)


class AlarmCreated(HueriseEvent):
    type: Literal[EventType.ALARM_CREATED] = EventType.ALARM_CREATED
    alarm: AlarmSnapshot


class AlarmUpdated(HueriseEvent):
    type: Literal[EventType.ALARM_UPDATED] = EventType.ALARM_UPDATED
    alarm: AlarmSnapshot
    changed: list[AlarmField] = Field(
        description="The fields this update actually moved."
    )


class AlarmDeleted(HueriseEvent):
    type: Literal[EventType.ALARM_DELETED] = EventType.ALARM_DELETED
    alarm_id: UUID


class NextAlarmChanged(HueriseEvent):
    """The alarm that will fire next is now a different one, or fires at a
    different time. Derived -- never emitted by hand."""

    type: Literal[EventType.NEXT_ALARM_CHANGED] = EventType.NEXT_ALARM_CHANGED
    alarm: AlarmSnapshot | None = Field(
        description="None when no enabled alarm remains."
    )
    scheduled_for: datetime | None


class OccurrenceScheduled(HueriseEvent):
    type: Literal[EventType.OCCURRENCE_SCHEDULED] = EventType.OCCURRENCE_SCHEDULED
    occurrence: OccurrenceSnapshot


class OccurrenceStarted(HueriseEvent):
    """The sunrise has begun. Everything a display needs to open its wake screen."""

    type: Literal[EventType.OCCURRENCE_STARTED] = EventType.OCCURRENCE_STARTED
    occurrence: OccurrenceSnapshot
    label: str
    room_name: str
    sunrise_seconds: int


class OccurrenceProgress(HueriseEvent):
    """One sunrise step. Fires per brightness change, so it carries no snapshot:
    the occurrence itself does not move while the sunrise runs."""

    type: Literal[EventType.OCCURRENCE_PROGRESS] = EventType.OCCURRENCE_PROGRESS
    occurrence_id: UUID
    alarm_id: UUID
    brightness: int
    step: int
    total_steps: int
    elapsed_seconds: int
    total_seconds: int

    @computed_field
    @property
    def percent(self) -> float:
        return round(100 * (self.step + 1) / self.total_steps, 1)


class OccurrenceRinging(HueriseEvent):
    type: Literal[EventType.OCCURRENCE_RINGING] = EventType.OCCURRENCE_RINGING
    occurrence_id: UUID
    alarm_id: UUID
    sound_id: UUID
    volume: int


class OccurrenceSnoozed(HueriseEvent):
    type: Literal[EventType.OCCURRENCE_SNOOZED] = EventType.OCCURRENCE_SNOOZED
    occurrence: OccurrenceSnapshot


class OccurrenceDismissed(HueriseEvent):
    type: Literal[EventType.OCCURRENCE_DISMISSED] = EventType.OCCURRENCE_DISMISSED
    occurrence: OccurrenceSnapshot


class OccurrenceSkipped(HueriseEvent):
    type: Literal[EventType.OCCURRENCE_SKIPPED] = EventType.OCCURRENCE_SKIPPED
    occurrence: OccurrenceSnapshot


class OccurrenceFailed(HueriseEvent):
    type: Literal[EventType.OCCURRENCE_FAILED] = EventType.OCCURRENCE_FAILED
    occurrence: OccurrenceSnapshot


type AnyHueriseEvent = Annotated[
    AlarmCreated
    | AlarmUpdated
    | AlarmDeleted
    | NextAlarmChanged
    | OccurrenceScheduled
    | OccurrenceStarted
    | OccurrenceProgress
    | OccurrenceRinging
    | OccurrenceSnoozed
    | OccurrenceDismissed
    | OccurrenceSkipped
    | OccurrenceFailed,
    Field(discriminator="type"),
]
