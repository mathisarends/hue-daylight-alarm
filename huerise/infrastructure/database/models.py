"""Central ORM schema.

All tables live here instead of next to the feature that owns them: the schema
is small enough that one place beats colocation, and Alembic sees the complete
metadata through a single import.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from huerise.infrastructure.database.types import UtcDateTime

# Spelled out rather than imported from the alarm domain: the schema module must
# stay free of feature imports, otherwise Alembic pulls the whole app in. A test
# pins these values to OccurrenceState.
OCCURRENCE_STATES = (
    "pending",
    "sunrise",
    "ringing",
    "snoozed",
    "dismissed",
    "skipped",
    "failed",
)

_OCCURRENCE_STATE_COLUMN = SAEnum(*OCCURRENCE_STATES, name="occurrence_state")


class DatabaseEntity(SQLModel):
    """Base for every table: a UUID primary key the generic repository can use."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)


class AlarmProfileModel(DatabaseEntity, table=True):
    """How an alarm behaves. Reusable across alarms."""

    __tablename__ = "alarm_profiles"

    name: str = Field(unique=True)
    is_default: bool = Field(default=False)

    intro_audio_file: str

    sunrise_scene_name: str
    sunrise_duration_minutes: int
    sunrise_brightness_start: int
    sunrise_brightness_end: int

    ringtone_audio_file: str
    ringtone_volume: int


class AlarmModel(DatabaseEntity, table=True):
    """The rule: when, where, with which profile."""

    __tablename__ = "alarms"

    label: str
    is_enabled: bool = Field(default=True, index=True)

    # Wall-clock time plus IANA zone, never a UTC instant: the concrete moment
    # is resolved per occurrence so alarms survive DST transitions.
    hour: int
    minute: int
    timezone: str
    recurrence_mask: int = Field(default=0)  # one bit per weekday, 0 = one-time

    profile_id: UUID = Field(foreign_key="alarm_profiles.id", index=True)
    room_name: str

    created_at: datetime = Field(sa_column=Column(UtcDateTime, nullable=False))


class AlarmOccurrenceModel(DatabaseEntity, table=True):
    """A single wake-up run. All runtime state lives here."""

    __tablename__ = "alarm_occurrences"
    __table_args__ = (
        UniqueConstraint("alarm_id", "scheduled_for", name="uq_occurrence_alarm_time"),
    )

    alarm_id: UUID = Field(foreign_key="alarms.id", index=True)

    scheduled_for: datetime = Field(
        sa_column=Column(UtcDateTime, nullable=False, index=True)
    )
    state: str = Field(
        sa_column=Column(_OCCURRENCE_STATE_COLUMN, nullable=False, index=True)
    )
    triggered_at: datetime | None = Field(default=None, sa_column=Column(UtcDateTime))
    finished_at: datetime | None = Field(default=None, sa_column=Column(UtcDateTime))
    snooze_count: int = Field(default=0)
    failure_reason: str | None = Field(default=None)
