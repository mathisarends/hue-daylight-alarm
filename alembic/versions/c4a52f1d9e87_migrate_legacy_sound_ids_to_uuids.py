"""migrate legacy sound ids to uuids

Revision ID: c4a52f1d9e87
Revises: b7d3e1f04c58
Create Date: 2026-08-04

"""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, UUID, uuid5

import sqlalchemy as sa

from alembic import op

revision: str = "c4a52f1d9e87"
down_revision: str | Sequence[str] | None = "b7d3e1f04c58"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = ("intro_sound_id", "ringtone_sound_id")
_CATEGORIES = ("wake_up", "get_up")


def _to_uuid(value: str) -> str:
    """Convert category/name and old file-name ids; leave UUIDs untouched."""
    try:
        return str(UUID(value))
    except ValueError:
        pass

    normalized = value.rsplit("/", maxsplit=1)[-1].rsplit(".", maxsplit=1)[0]
    for category in _CATEGORIES:
        category_prefix = f"{category}/"
        file_prefix = f"{category.replace('_', '-')}-"
        if value.startswith(category_prefix):
            name = value.removeprefix(category_prefix).rsplit(".", maxsplit=1)[0]
            break
        if normalized.startswith(file_prefix):
            name = normalized.removeprefix(file_prefix)
            break
    else:
        return str(uuid5(NAMESPACE_URL, f"huerise:sound:legacy:{normalized}"))

    return str(uuid5(NAMESPACE_URL, f"huerise:sound:{category}/{name}"))


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(f"SELECT id, {', '.join(_COLUMNS)} FROM alarm_profiles")
    ).mappings()
    for row in rows:
        values = {column: _to_uuid(str(row[column])) for column in _COLUMNS}
        bind.execute(
            sa.text(
                "UPDATE alarm_profiles "
                "SET intro_sound_id = :intro_sound_id, "
                "ringtone_sound_id = :ringtone_sound_id WHERE id = :id"
            ),
            {"id": row["id"], **values},
        )


def downgrade() -> None:
    # UUIDs are canonical and cannot reconstruct arbitrary legacy identifiers.
    pass
