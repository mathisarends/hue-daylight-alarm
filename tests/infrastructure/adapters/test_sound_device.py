from unittest.mock import AsyncMock, MagicMock

import pytest

from huerise.features.devices.infrastructure.sound_device import SoundDeviceAudioPlayer
from huerise.infrastructure.storage import StorageBackend


@pytest.mark.parametrize(
    ("audio_file", "expected_path"),
    [
        ("wake-up-bowls.mp3", "wake_up_sounds/wake-up-bowls.mp3"),
        ("get-up-aurora.mp3", "get_up_sounds/get-up-aurora.mp3"),
        ("custom.mp3", "custom.mp3"),
        ("other/custom.mp3", "other/custom.mp3"),
    ],
)
def test_resolves_storage_path(audio_file: str, expected_path: str) -> None:
    assert SoundDeviceAudioPlayer._storage_path(audio_file) == expected_path


async def test_downloads_audio_from_storage() -> None:
    storage = MagicMock(spec=StorageBackend)
    storage.download_bytes = AsyncMock(return_value=b"audio data")
    player = SoundDeviceAudioPlayer(storage)
    player.stop = AsyncMock()
    player._play_blocking = MagicMock()

    await player.play("wake-up-bowls.mp3", volume=40)

    storage.download_bytes.assert_awaited_once_with("wake_up_sounds/wake-up-bowls.mp3")
    player._play_blocking.assert_called_once_with(b"audio data")
