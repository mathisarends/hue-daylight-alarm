# All tables live here instead of next to the feature that owns them: the schema
# is small enough that one place beats colocation, and Alembic sees the complete
# metadata through a single import.

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from huerise.infrastructure.database.types import UtcDateTime

# Spelled out rather than imported from the alarm domain: the schema module must
# stay free of feature imports, otherwise Alembic pulls the whole app in. Tests
# pin these values to OccurrenceState and AlarmDefect.
OCCURRENCE_STATES = (
    "pending",
    "sunrise",
    "dismissed",
    "skipped",
    "failed",
)

ALARM_DEFECTS = (
    "room_missing",
    "scene_missing",
)

_OCCURRENCE_STATE_COLUMN = SAEnum(*OCCURRENCE_STATES, name="occurrence_state")
_ALARM_DEFECT_COLUMN = SAEnum(*ALARM_DEFECTS, name="alarm_defect")


class DatabaseEntity(SQLModel):
    """Base for every table: a UUID primary key the generic repository can use."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)


class UserModel(DatabaseEntity, table=True):
    __tablename__ = "users"

    username: str = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(sa_column=Column(UtcDateTime, nullable=False))


class RefreshTokenModel(DatabaseEntity, table=True):
    __tablename__ = "refresh_tokens"

    user_id: UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(unique=True, index=True)
    created_at: datetime = Field(sa_column=Column(UtcDateTime, nullable=False))
    expires_at: datetime = Field(sa_column=Column(UtcDateTime, nullable=False))
    revoked_at: datetime | None = Field(default=None, sa_column=Column(UtcDateTime))


class HueBridgeSelectionModel(DatabaseEntity, table=True):
    __tablename__ = "hue_bridge_selection"

    bridge_id: str = Field(unique=True)
    ip_address: str
    app_key: str | None = None


class AlarmProfileModel(DatabaseEntity, table=True):
    """How an alarm behaves. Reusable across alarms."""

    __tablename__ = "alarm_profiles"

    name: str = Field(unique=True)
    is_default: bool = Field(default=False)

    sunrise_scene_id: UUID
    sunrise_scene_name: str
    sunrise_duration_minutes: int
    sunrise_brightness_start: int
    sunrise_brightness_end: int


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
    room_id: UUID
    room_name: str

    # NULL while the room and scene still resolve on the bridge.
    defect: str | None = Field(default=None, sa_column=Column(_ALARM_DEFECT_COLUMN))

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
    failure_reason: str | None = Field(default=None)
