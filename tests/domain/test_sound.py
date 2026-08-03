import pytest

from huerise.features.devices.domain import Sound, SoundCategory


@pytest.mark.parametrize(
    ("storage_path", "expected_id", "expected_category"),
    [
        ("wake_up_sounds/wake-up-bowls.mp3", "wake_up/bowls", SoundCategory.WAKE_UP),
        ("get_up_sounds/get-up-aurora.mp3", "get_up/aurora", SoundCategory.GET_UP),
        # A file that never got the category prefix still belongs to its folder.
        ("get_up_sounds/aurora.wav", "get_up/aurora", SoundCategory.GET_UP),
    ],
)
def test_derives_its_id_from_category_and_file_name(
    storage_path: str, expected_id: str, expected_category: SoundCategory
) -> None:
    sound = Sound.from_storage_path(storage_path)

    assert sound is not None
    assert sound.id == expected_id
    assert sound.category is expected_category
    assert sound.storage_path == storage_path


@pytest.mark.parametrize(
    "storage_path",
    ["other_sounds/custom.mp3", "custom.mp3", "wake_up_sounds/wake-up-.mp3"],
)
def test_ignores_paths_outside_a_known_category(storage_path: str) -> None:
    assert Sound.from_storage_path(storage_path) is None
