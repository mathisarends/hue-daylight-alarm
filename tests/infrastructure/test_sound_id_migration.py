from pathlib import Path
from runpy import run_path
from uuid import UUID

_migration = run_path(
    str(
        Path(__file__).parents[2]
        / "alembic/versions/c4a52f1d9e87_migrate_legacy_sound_ids_to_uuids.py"
    )
)


def test_migrates_category_sound_ids_to_catalog_uuids() -> None:
    assert _migration["_to_uuid"]("wake_up/bowls") == (
        "1693baba-146e-5b14-acf2-6f76554f36e9"
    )
    assert _migration["_to_uuid"]("get_up/aurora") == (
        "5c0806e7-7162-5be7-948e-33d349bde4a8"
    )


def test_migration_leaves_uuid_sound_ids_unchanged() -> None:
    sound_id = UUID("5c0806e7-7162-5be7-948e-33d349bde4a8")

    assert _migration["_to_uuid"](str(sound_id)) == str(sound_id)
