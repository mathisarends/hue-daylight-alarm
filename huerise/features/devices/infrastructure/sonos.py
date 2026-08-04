import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from huerise.features.devices.application import AudioPlayer, SoundCatalog
from huerise.features.devices.domain import AudioOutput, AudioOutputUnavailableError
from huerise.infrastructure.storage import StorageBackend

if TYPE_CHECKING:
    from sonosify import SonosClient

logger = logging.getLogger(__name__)

_LINK_LIFETIME = timedelta(hours=6)
_POLL_INTERVAL = 2.0

_PLAYING_STATES = frozenset({"PLAYING", "TRANSITIONING"})


class SonosAudioPlayer(AudioPlayer):
    """Plays through a Sonos speaker over UPnP on the local network.

    The speaker fetches the audio itself, so the sound is handed over as a
    presigned storage link rather than as bytes. The connected client comes
    from the composition root, so discovery failures stop app startup.
    """

    def __init__(
        self,
        catalog: SoundCatalog,
        storage: StorageBackend,
        client: SonosClient,
    ) -> None:
        self._catalog = catalog
        self._storage = storage
        self._client = client
        self._stopped = asyncio.Event()

    async def play(self, sound_id: UUID, volume: int) -> None:
        sound = await self._catalog.get(sound_id)
        url = await self._storage.public_url(sound.storage_path, _LINK_LIFETIME)
        self._stopped.clear()

        async with _translated_errors():
            await self._client.set_volume(volume)
            logger.info("Playing %s on Sonos speaker %s", sound.name, self._client.ip)
            await self._client.play_uri(url, title=sound.name)
            await self._await_end(self._client)

    async def stop(self) -> None:
        self._stopped.set()
        async with _translated_errors():
            await self._client.stop()

    async def set_volume(self, volume: int) -> None:
        async with _translated_errors():
            await self._client.set_volume(volume)

    async def _await_end(self, speaker: SonosClient) -> None:
        """Return once the speaker stopped, so ``play`` outlasts the sound."""
        while not self._stopped.is_set():
            await asyncio.sleep(_POLL_INTERVAL)
            info = await speaker.get_transport_info()
            if info.state is None or info.state not in _PLAYING_STATES:
                return


@asynccontextmanager
async def _translated_errors() -> AsyncGenerator[None]:
    """Speaker trouble is an unavailable output, not a bug in the caller."""
    from sonosify import SonosifyError

    try:
        yield
    except SonosifyError as error:
        raise AudioOutputUnavailableError(AudioOutput.SONOS, str(error)) from error
