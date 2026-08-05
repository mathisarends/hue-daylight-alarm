"""flag alarms whose Hue room or scene no longer resolves

Revision ID: f5c81a30d7b2
Revises: e8a6f2d91b47
Create Date: 2026-08-05

Existing rows start out healthy: the bridge is only ever consulted while the
app runs, so a defect is recorded the first time a change event proves one.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f5c81a30d7b2"
down_revision: str | Sequence[str] | None = "e8a6f2d91b47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DEFECTS = ("room_missing", "scene_missing")


def upgrade() -> None:
    with op.batch_alter_table("alarms") as batch_op:
        batch_op.add_column(
            sa.Column(
                "defect",
                sa.Enum(*_DEFECTS, name="alarm_defect"),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("alarms") as batch_op:
        batch_op.drop_column("defect")
