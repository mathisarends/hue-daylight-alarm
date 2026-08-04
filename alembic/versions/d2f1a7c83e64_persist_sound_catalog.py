from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa

from alembic import op

revision: str = "d2f1a7c83e64"
down_revision: str | Sequence[str] | None = "c4a52f1d9e87"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SOUNDS = (
    (
        "5c0806e7-7162-5be7-948e-33d349bde4a8",
        "aurora",
        "get_up",
        "get_up_sounds/get-up-aurora.mp3",
    ),
    (
        "b0395e47-5f6e-5001-b629-7a5730a9e1b5",
        "blossom",
        "get_up",
        "get_up_sounds/get-up-blossom.mp3",
    ),
    (
        "bb1fb63e-0726-5939-a985-5f958b3b8427",
        "retreat",
        "get_up",
        "get_up_sounds/get-up-retreat.mp3",
    ),
    (
        "e02db7f4-9286-5c46-9dc0-de8635c69928",
        "shake",
        "get_up",
        "get_up_sounds/get-up-shake.mp3",
    ),
    (
        "5730da72-6b98-5b0c-b737-3c4ab1fdfefa",
        "shimmer",
        "get_up",
        "get_up_sounds/get-up-shimmer.mp3",
    ),
    (
        "2796e704-1384-5dd4-b0ab-e7b0c129cedd",
        "time",
        "get_up",
        "get_up_sounds/get-up-time.mp3",
    ),
    (
        "db72b724-97e9-5d0e-8368-a002d96cc53f",
        "wisdom",
        "get_up",
        "get_up_sounds/get-up-wisdom.mp3",
    ),
    (
        "1693baba-146e-5b14-acf2-6f76554f36e9",
        "bowls",
        "wake_up",
        "wake_up_sounds/wake-up-bowls.mp3",
    ),
    (
        "0d46a869-b105-52a4-a2e7-7df2ab4f5f69",
        "cherry",
        "wake_up",
        "wake_up_sounds/wake-up-cherry.mp3",
    ),
    (
        "01558e8b-30e6-5e62-8628-f04115fce1ab",
        "focus",
        "wake_up",
        "wake_up_sounds/wake-up-focus.mp3",
    ),
    (
        "a7c96c55-c41f-52a3-9c81-012cc83c99ef",
        "fountain",
        "wake_up",
        "wake_up_sounds/wake-up-fountain.mp3",
    ),
    (
        "a1a17215-9593-5d31-9db3-0c27e7dcd191",
        "galaxy",
        "wake_up",
        "wake_up_sounds/wake-up-galaxy.mp3",
    ),
    (
        "4b8afa3c-8898-5b5c-833b-4171ceacc90c",
        "gong",
        "wake_up",
        "wake_up_sounds/wake-up-gong.mp3",
    ),
    (
        "e0272624-13b9-5365-a689-e5f0efb510cc",
        "jungle",
        "wake_up",
        "wake_up_sounds/wake-up-jungle.mp3",
    ),
    (
        "bb804011-6bb8-5b4e-9d90-ebe5e11becb0",
        "mist",
        "wake_up",
        "wake_up_sounds/wake-up-mist.mp3",
    ),
    (
        "98feae9e-9cce-52c7-b16a-10b30d21314e",
        "paradise",
        "wake_up",
        "wake_up_sounds/wake-up-paradise.mp3",
    ),
    (
        "57d0bc86-8bd4-54f0-a671-fe7cee69ea8b",
        "serene",
        "wake_up",
        "wake_up_sounds/wake-up-serene.mp3",
    ),
    (
        "c28c2041-0f66-523c-ab64-26ae02412021",
        "train",
        "wake_up",
        "wake_up_sounds/wake-up-train.mp3",
    ),
)


def upgrade() -> None:
    sounds = op.create_table(
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
    created_at = datetime.now(UTC)
    op.bulk_insert(
        sounds,
        [
            {
                "id": UUID(sound_id),
                "name": name,
                "category": category,
                "storage_path": storage_path,
                "created_at": created_at,
            }
            for sound_id, name, category, storage_path in _SOUNDS
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_sounds_category", table_name="sounds")
    op.drop_table("sounds")
