"""persist Sonos speaker selection

Revision ID: a9e4c1b7d2f6
Revises: f5c81a30d7b2
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "a9e4c1b7d2f6"
down_revision: str | Sequence[str] | None = "f5c81a30d7b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sonos_speaker_selection",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("speaker_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("speaker_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("ip_address", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("group_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("is_coordinator", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("speaker_id"),
    )


def downgrade() -> None:
    op.drop_table("sonos_speaker_selection")
