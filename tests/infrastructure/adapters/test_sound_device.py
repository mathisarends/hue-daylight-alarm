from unittest.mock import AsyncMock, MagicMock

from huerise.features.devices.application import SoundCatalog
from huerise.features.devices.domain import Sound, SoundCategory
from huerise.features.devices.infrastructure.sound_device import SoundDeviceAudioPlayer
from huerise.infrastructure.storage import StorageBackend


async def test_downloads_the_sound_the_id_points_at() -> None:
    catalog = MagicMock(spec=SoundCatalog)
    catalog.get = AsyncMock(
        return_value=Sound(
            id="wake_up/bowls",
            name="bowls",
            category=SoundCategory.WAKE_UP,
            storage_path="wake_up_sounds/wake-up-bowls.mp3",
        )
    )
    storage = MagicMock(spec=StorageBackend)
    storage.download_bytes = AsyncMock(return_value=b"audio data")

    player = SoundDeviceAudioPlayer(catalog, storage)
    player._play_blocking = MagicMock()

    await player.play("wake_up/bowls", volume=40)

    storage.download_bytes.assert_awaited_once_with("wake_up_sounds/wake-up-bowls.mp3")
    player._play_blocking.assert_called_once_with(b"audio data")
