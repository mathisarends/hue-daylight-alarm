"""address Hue rooms and scenes by stable resource ID

Revision ID: e8a6f2d91b47
Revises: d2f1a7c83e64
Create Date: 2026-08-04

Hue resource names are retained as display metadata. Existing installations
cannot derive bridge-local resource IDs from those names while migrating, so
legacy rows receive the nil UUID. Re-selecting their room/scene through the API
replaces it with the real bridge UUID; no user-facing names are discarded.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e8a6f2d91b47"
down_revision: str | Sequence[str] | None = "d2f1a7c83e64"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UNRESOLVED_ID = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    with op.batch_alter_table("alarm_profiles") as batch_op:
        batch_op.add_column(
            sa.Column(
                "sunrise_scene_id",
                sa.Uuid(),
                nullable=False,
                server_default=_UNRESOLVED_ID,
            )
        )
    with op.batch_alter_table("alarm_profiles") as batch_op:
        batch_op.alter_column("sunrise_scene_id", server_default=None)

    with op.batch_alter_table("alarms") as batch_op:
        batch_op.add_column(
            sa.Column(
                "room_id",
                sa.Uuid(),
                nullable=False,
                server_default=_UNRESOLVED_ID,
            )
        )
    with op.batch_alter_table("alarms") as batch_op:
        batch_op.alter_column("room_id", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("alarms") as batch_op:
        batch_op.drop_column("room_id")
    with op.batch_alter_table("alarm_profiles") as batch_op:
        batch_op.drop_column("sunrise_scene_id")
