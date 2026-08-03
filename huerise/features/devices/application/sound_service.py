import asyncio
import logging
from uuid import UUID

from huerise.features.devices.application.ports import AudioPlayer
from huerise.features.devices.application.sound_catalog import SoundCatalog
from huerise.features.devices.domain import Sound, SoundCategory

logger = logging.getLogger(__name__)

PREVIEW_VOLUME = 60

# Playback outlives the request that started it, so the tasks need an owner
# other than the (request-scoped) service instance.
_previews: set[asyncio.Task[None]] = set()


class SoundService:
    def __init__(self, catalog: SoundCatalog, audio: AudioPlayer) -> None:
        self._catalog = catalog
        self._audio = audio

    async def list_sounds(self, category: SoundCategory | None = None) -> list[Sound]:
        return await self._catalog.list_sounds(category)

    async def preview(self, sound_id: UUID, volume: int = PREVIEW_VOLUME) -> Sound:
        """Start playback in the background and return the sound being played."""
        sound = await self._catalog.get(sound_id)
        logger.info("Previewing sound %s at volume %d", sound.id, volume)

        await self._audio.stop()
        task = asyncio.create_task(self._audio.play(sound.id, volume))
        _previews.add(task)
        task.add_done_callback(_previews.discard)
        return sound

    async def stop(self) -> None:
        logger.info("Stopping playback")
        await self._audio.stop()

    async def set_volume(self, volume: int) -> None:
        logger.info("Setting volume to %d", volume)
        await self._audio.set_volume(volume)
