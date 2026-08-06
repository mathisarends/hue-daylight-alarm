"""persist Hue Bridge selection

Revision ID: c7a2d8e41f90
Revises: a9e4c1b7d2f6
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "c7a2d8e41f90"
down_revision: str | Sequence[str] | None = "a9e4c1b7d2f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hue_bridge_selection",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("bridge_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("ip_address", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("app_key", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bridge_id"),
    )


def downgrade() -> None:
    op.drop_table("hue_bridge_selection")
