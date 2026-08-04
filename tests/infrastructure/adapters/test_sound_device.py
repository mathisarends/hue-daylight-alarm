from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from huerise.features.devices.domain import Sound, SoundCategory, SoundRepository
from huerise.features.devices.infrastructure.sound_device import SoundDeviceAudioPlayer
from huerise.infrastructure.storage import StorageBackend


async def test_downloads_the_sound_the_id_points_at() -> None:
    sounds = MagicMock(spec=SoundRepository)
    sounds.get = AsyncMock(
        return_value=Sound(
            id=UUID("1693baba-146e-5b14-acf2-6f76554f36e9"),
            name="bowls",
            category=SoundCategory.WAKE_UP,
            storage_path="wake_up_sounds/wake-up-bowls.mp3",
        )
    )
    storage = MagicMock(spec=StorageBackend)
    storage.download_bytes = AsyncMock(return_value=b"audio data")

    player = SoundDeviceAudioPlayer(sounds, storage)
    player._play_blocking = MagicMock()

    await player.play(UUID("1693baba-146e-5b14-acf2-6f76554f36e9"), volume=40)

    storage.download_bytes.assert_awaited_once_with("wake_up_sounds/wake-up-bowls.mp3")
    player._play_blocking.assert_called_once_with(b"audio data")
