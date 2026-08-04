from pathlib import Path
from runpy import run_path
from uuid import UUID

from huerise.features.devices.domain import Sound

_migration = run_path(
    str(
        Path(__file__).parents[2]
        / "alembic/versions/c4a52f1d9e87_migrate_legacy_sound_ids_to_uuids.py"
    )
)


def test_migrates_category_sound_ids_to_catalog_uuids() -> None:
    bowls = Sound.from_storage_path("wake_up_sounds/wake-up-bowls.mp3")
    aurora = Sound.from_storage_path("get_up_sounds/get-up-aurora.mp3")
    assert bowls is not None
    assert aurora is not None

    assert _migration["_to_uuid"]("wake_up/bowls") == str(bowls.id)
    assert _migration["_to_uuid"]("get_up/aurora") == str(aurora.id)


def test_migration_leaves_uuid_sound_ids_unchanged() -> None:
    sound_id = UUID("5c0806e7-7162-5be7-948e-33d349bde4a8")

    assert _migration["_to_uuid"](str(sound_id)) == str(sound_id)
