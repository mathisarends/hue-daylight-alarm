"""scope down to light automation

Huerise now only runs the Hue sunrise ramp: no intro/ringtone sound, no
Sonos output, and no separate ringing/snoozed phase to wait through or
postpone. Existing `ringing`/`snoozed` occurrences are folded into
`sunrise` before the state column's check constraint is narrowed, since a
running or postponed sunrise is the closest surviving state to either.

Revision ID: b3e7c92a1f04
Revises: fbcbce7a1473
Create Date: 2026-08-30

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b3e7c92a1f04"
down_revision: str | Sequence[str] | None = "fbcbce7a1473"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_STATE = sa.Enum(
    "pending",
    "sunrise",
    "ringing",
    "snoozed",
    "dismissed",
    "skipped",
    "failed",
    name="occurrence_state",
)
_NEW_STATE = sa.Enum(
    "pending",
    "sunrise",
    "dismissed",
    "skipped",
    "failed",
    name="occurrence_state",
)


def upgrade() -> None:
    op.execute(
        "UPDATE alarm_occurrences SET state = 'sunrise' "
        "WHERE state IN ('ringing', 'snoozed')"
    )

    with op.batch_alter_table("alarm_occurrences") as batch:
        batch.alter_column("state", existing_type=_OLD_STATE, type_=_NEW_STATE)
        batch.drop_column("snooze_count")

    with op.batch_alter_table("alarm_profiles") as batch:
        batch.drop_column("intro_sound_id")
        batch.drop_column("ringtone_sound_id")
        batch.drop_column("ringtone_volume")

    op.drop_index("ix_sounds_category", table_name="sounds")
    op.drop_table("sounds")
    op.drop_table("sonos_speaker_selection")


def downgrade() -> None:
    op.create_table(
        "sonos_speaker_selection",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("speaker_id", sa.String(), nullable=False),
        sa.Column("speaker_name", sa.String(), nullable=False),
        sa.Column("ip_address", sa.String(), nullable=False),
        sa.Column("group_id", sa.String(), nullable=True),
        sa.Column("is_coordinator", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("speaker_id"),
    )
    op.create_table(
        "sounds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category", "name", name="uq_sounds_category_name"),
        sa.UniqueConstraint("storage_path"),
    )
    op.create_index("ix_sounds_category", "sounds", ["category"])

    with op.batch_alter_table("alarm_profiles") as batch:
        batch.add_column(sa.Column("intro_sound_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("ringtone_sound_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("ringtone_volume", sa.Integer(), nullable=True))

    with op.batch_alter_table("alarm_occurrences") as batch:
        batch.add_column(
            sa.Column(
                "snooze_count", sa.Integer(), nullable=False, server_default="0"
            )
        )
        batch.alter_column("state", existing_type=_NEW_STATE, type_=_OLD_STATE)
