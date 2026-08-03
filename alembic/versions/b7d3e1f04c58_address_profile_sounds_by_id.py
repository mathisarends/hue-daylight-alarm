"""address profile sounds by id

Profiles referenced a bare file name (``wake-up-bowls.mp3``) that only the
audio player knew how to turn into a storage path. They now store the id the
sounds API hands out (``wake_up/bowls``), so what a client picks is exactly
what gets persisted.

Revision ID: b7d3e1f04c58
Revises: a1c7f4d9b2e3
Create Date: 2026-08-03

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "b7d3e1f04c58"
down_revision: Union[str, Sequence[str], None] = "a1c7f4d9b2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Spelled out rather than imported from the devices feature: migrations must
# keep running even after the categories change.
_CATEGORIES = ("wake_up", "get_up")

_RENAMES = (
    ("intro_audio_file", "intro_sound_id"),
    ("ringtone_audio_file", "ringtone_sound_id"),
)


def _to_sound_id(file_name: str) -> str:
    name = file_name.rsplit(".", maxsplit=1)[0]
    for category in _CATEGORIES:
        prefix = f"{category.replace('_', '-')}-"
        if name.startswith(prefix):
            return f"{category}/{name.removeprefix(prefix)}"
    return name


def _to_file_name(sound_id: str) -> str:
    category, separator, name = sound_id.partition("/")
    if not separator or category not in _CATEGORIES:
        return sound_id
    return f"{category.replace('_', '-')}-{name}.mp3"


def _convert(columns: Sequence[str], convert) -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(f"SELECT id, {', '.join(columns)} FROM alarm_profiles")
    ).all()
    assignments = ", ".join(f"{column} = :{column}" for column in columns)
    for row in rows:
        bind.execute(
            sa.text(f"UPDATE alarm_profiles SET {assignments} WHERE id = :id"),
            {"id": row.id}
            | {column: convert(getattr(row, column)) for column in columns},
        )


def upgrade() -> None:
    with op.batch_alter_table("alarm_profiles") as batch:
        for old_name, new_name in _RENAMES:
            batch.alter_column(old_name, new_column_name=new_name)

    _convert([new_name for _, new_name in _RENAMES], _to_sound_id)


def downgrade() -> None:
    _convert([new_name for _, new_name in _RENAMES], _to_file_name)

    with op.batch_alter_table("alarm_profiles") as batch:
        for old_name, new_name in _RENAMES:
            batch.alter_column(new_name, new_column_name=old_name)
