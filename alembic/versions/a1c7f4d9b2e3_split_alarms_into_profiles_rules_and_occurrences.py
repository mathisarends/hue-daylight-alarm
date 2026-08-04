"""split alarms into profiles, rules and occurrences

Replaces the single flat ``alarms`` table with three tables that have
different lifecycles: reusable profiles, the wake-up rule, and the runtime
state of each individual run.

The old table is dropped: alarm times were stored without a timezone and
without a profile reference, so there is nothing to migrate them onto.

Revision ID: a1c7f4d9b2e3
Revises: 6e482063878e
Create Date: 2026-08-03

"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "a1c7f4d9b2e3"
down_revision: str | Sequence[str] | None = "6e482063878e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_PROFILE_ID = UUID("0198f0c4-0000-7000-8000-000000000001")

_OCCURRENCE_STATE = sa.Enum(
    "pending",
    "sunrise",
    "ringing",
    "snoozed",
    "dismissed",
    "skipped",
    "failed",
    name="occurrence_state",
)


def upgrade() -> None:
    op.drop_table("alarms")

    profiles = op.create_table(
        "alarm_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column(
            "intro_audio_file", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column(
            "sunrise_scene_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("sunrise_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("sunrise_brightness_start", sa.Integer(), nullable=False),
        sa.Column("sunrise_brightness_end", sa.Integer(), nullable=False),
        sa.Column(
            "ringtone_audio_file", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("ringtone_volume", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "alarms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("label", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("hour", sa.Integer(), nullable=False),
        sa.Column("minute", sa.Integer(), nullable=False),
        sa.Column("timezone", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("recurrence_mask", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("room_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["alarm_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alarms_is_enabled", "alarms", ["is_enabled"])
    op.create_index("ix_alarms_profile_id", "alarms", ["profile_id"])

    op.create_table(
        "alarm_occurrences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("alarm_id", sa.Uuid(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("state", _OCCURRENCE_STATE, nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snooze_count", sa.Integer(), nullable=False),
        sa.Column("failure_reason", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(["alarm_id"], ["alarms.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "alarm_id", "scheduled_for", name="uq_occurrence_alarm_time"
        ),
    )
    op.create_index("ix_alarm_occurrences_alarm_id", "alarm_occurrences", ["alarm_id"])
    op.create_index(
        "ix_alarm_occurrences_scheduled_for", "alarm_occurrences", ["scheduled_for"]
    )
    op.create_index("ix_alarm_occurrences_state", "alarm_occurrences", ["state"])

    # Every alarm needs a profile, so ship one out of the box.
    op.bulk_insert(
        profiles,
        [
            {
                "id": DEFAULT_PROFILE_ID,
                "name": "Standard",
                "is_default": True,
                "intro_audio_file": "wake-up-bowls.mp3",
                "sunrise_scene_name": "Tageslichtwecker",
                "sunrise_duration_minutes": 7,
                "sunrise_brightness_start": 1,
                "sunrise_brightness_end": 100,
                "ringtone_audio_file": "get-up-aurora.mp3",
                "ringtone_volume": 80,
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("alarm_occurrences")
    op.drop_table("alarms")
    op.drop_table("alarm_profiles")
    _OCCURRENCE_STATE.drop(op.get_bind(), checkfirst=True)

    op.create_table(
        "alarms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("label", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("alarm_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("series_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("schedule_hour", sa.Integer(), nullable=False),
        sa.Column("schedule_minute", sa.Integer(), nullable=False),
        sa.Column(
            "schedule_recurrence", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column(
            "intro_audio_file", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column(
            "sunrise_room_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column(
            "sunrise_scene_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("sunrise_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("sunrise_brightness_start", sa.Integer(), nullable=False),
        sa.Column("sunrise_brightness_end", sa.Integer(), nullable=False),
        sa.Column("sunrise_steps", sa.Integer(), nullable=False),
        sa.Column(
            "ringtone_audio_file", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("ringtone_volume", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
