import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from huerise.features.devices.application import AudioPlayer, SoundCatalog
from huerise.features.devices.domain import AudioOutput, AudioOutputUnavailableError
from huerise.features.devices.infrastructure.settings import SonosSettings
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
    presigned storage link rather than as bytes. Discovery is deferred to the
    first playback: with the local output selected there is no speaker to find.
    """

    def __init__(
        self,
        catalog: SoundCatalog,
        storage: StorageBackend,
        settings: SonosSettings,
    ) -> None:
        self._catalog = catalog
        self._storage = storage
        self._settings = settings
        self._client: SonosClient | None = None
        self._lock = asyncio.Lock()
        self._stopped = asyncio.Event()

    async def play(self, sound_id: UUID, volume: int) -> None:
        sound = await self._catalog.get(sound_id)
        url = await self._storage.public_url(sound.storage_path, _LINK_LIFETIME)
        self._stopped.clear()

        async with _translated_errors():
            speaker = await self._connect()
            await speaker.set_volume(volume)
            logger.info("Playing %s on Sonos speaker %s", sound.name, speaker.ip)
            await speaker.play_uri(url, title=sound.name)
            await self._await_end(speaker)

    async def stop(self) -> None:
        self._stopped.set()
        if self._client is None:
            return
        async with _translated_errors():
            await self._client.stop()

    async def set_volume(self, volume: int) -> None:
        async with _translated_errors():
            speaker = await self._connect()
            await speaker.set_volume(volume)

    async def close(self) -> None:
        if self._client is None:
            return
        await self._client.close()
        self._client = None

    async def _connect(self) -> SonosClient:
        """The speaker, discovered once and kept for later playbacks."""
        async with self._lock:
            if self._client is not None:
                return self._client

            # Imported here so the UPnP stack stays out of a run that only
            # ever plays locally.
            from sonosify import SonosController

            controller = SonosController(
                discovery_timeout=self._settings.discovery_timeout
            )
            self._client = await controller.client(
                self._settings.room_name, ip=self._settings.ip
            )
            logger.info(
                "Connected to Sonos speaker %s at %s",
                await self._client.get_room_name(),
                self._client.ip,
            )
            return self._client

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
