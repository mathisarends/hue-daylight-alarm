from datetime import UTC
from uuid import UUID

from huerise.features.devices.domain import Sound, SoundCategory


def test_keeps_explicit_metadata_independent_of_the_storage_path() -> None:
    sound = Sound(
        id=UUID("1693baba-146e-5b14-acf2-6f76554f36e9"),
        name="Morning bowls",
        category=SoundCategory.WAKE_UP,
        storage_path="private/custom/opaque-key.mp3",
    )

    assert sound.id == UUID("1693baba-146e-5b14-acf2-6f76554f36e9")
    assert sound.name == "Morning bowls"
    assert sound.category is SoundCategory.WAKE_UP
    assert sound.storage_path == "private/custom/opaque-key.mp3"
    assert sound.created_at.tzinfo is UTC
