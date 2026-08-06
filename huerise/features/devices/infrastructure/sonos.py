import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from huerise.features.devices.application import AudioPlayer, SonosSpeakerSelector
from huerise.features.devices.domain import (
    AudioOutput,
    AudioOutputUnavailableError,
    SonosSpeaker,
    SoundRepository,
)
from huerise.infrastructure.storage import StorageBackend

if TYPE_CHECKING:
    from sonosify import SonosClient, SonosController
    from sonosify.models import Speaker
    from sonosify.topology import SonosSystem

logger = logging.getLogger(__name__)

_LINK_LIFETIME = timedelta(hours=6)
_POLL_INTERVAL = 2.0

_PLAYING_STATES = frozenset({"PLAYING", "TRANSITIONING"})


class SonosAudioPlayer(AudioPlayer, SonosSpeakerSelector):
    """Plays through a Sonos speaker over UPnP on the local network.

    The speaker fetches the audio itself, so the sound is handed over as a
    presigned storage link rather than as bytes.
    """

    def __init__(
        self,
        sounds: SoundRepository,
        storage: StorageBackend,
        controller: SonosController,
    ) -> None:
        self._sounds = sounds
        self._storage = storage
        self._controller = controller
        self._client: SonosClient | None = None
        self._selected_speaker: SonosSpeaker | None = None
        self._lock = asyncio.Lock()
        self._stopped = asyncio.Event()

    @property
    def selected_speaker(self) -> SonosSpeaker | None:
        return self._selected_speaker

    async def discover_speakers(self) -> tuple[SonosSpeaker, ...]:
        async with self._lock, _translated_errors():
            system = await self._controller.discover()
            return _speakers_from_system(system)

    async def select_speaker(self, speaker_id: str) -> SonosSpeaker:
        async with self._lock, _translated_errors():
            system = self._controller.system or await self._controller.discover()
            speaker = next(
                (
                    candidate
                    for candidate in system.speakers
                    if _speaker_id(candidate) == speaker_id
                ),
                None,
            )
            if speaker is None:
                raise AudioOutputUnavailableError(
                    AudioOutput.SONOS, f"speaker '{speaker_id}' was not discovered"
                )
            selected = _speaker_from_system(speaker, system)
            client = system.client(ip=speaker.ip, coordinator=True)
            await client.get_room_name()
            await self._replace_client(client, selected)
            return selected

    async def restore_speaker(self, speaker: SonosSpeaker) -> SonosSpeaker:
        async with self._lock, _translated_errors():
            client = await self._controller.client(ip=speaker.ip_address)
            name = await client.get_room_name()
            restored = SonosSpeaker(
                id=speaker.id,
                name=name,
                ip_address=speaker.ip_address,
                group_id=speaker.group_id,
                is_coordinator=speaker.is_coordinator,
            )
            await self._replace_client(client, restored)
            return restored

    async def configure(self, room: str | None, ip: str | None) -> SonosSpeaker:
        async with self._lock, _translated_errors():
            if ip is None:
                system = await self._controller.discover()
                speaker = system.find(room)
                selected = _speaker_from_system(speaker, system)
                client = system.client(ip=speaker.ip, coordinator=True)
            else:
                client = await self._controller.client(room, ip=ip)
                name = await client.get_room_name()
                selected = SonosSpeaker(
                    id=client.uid or ip,
                    name=name,
                    ip_address=ip,
                )
            if ip is None:
                await client.get_room_name()
            await self._replace_client(client, selected)
            return selected

    async def play(self, sound_id: UUID, volume: int) -> None:
        sound = await self._sounds.get(sound_id)
        url = await self._storage.public_url(sound.storage_path, _LINK_LIFETIME)

        async with self._lock, _translated_errors():
            client = self._require_client()
            stopped = asyncio.Event()
            self._stopped = stopped
            await client.set_volume(volume)
            logger.info("Playing %s on Sonos speaker %s", sound.name, client.ip)
            await client.play_uri(url, title=sound.name)
        async with _translated_errors():
            await self._await_end(client, stopped)

    async def stop(self) -> None:
        async with self._lock, _translated_errors():
            self._stopped.set()
            if self._client is not None:
                await self._client.stop()

    async def set_volume(self, volume: int) -> None:
        async with self._lock, _translated_errors():
            await self._require_client().set_volume(volume)

    async def close(self) -> None:
        async with self._lock:
            self._stopped.set()
            if self._client is not None:
                await self._client.close()
                self._client = None

    def _require_client(self) -> SonosClient:
        if self._client is None:
            raise AudioOutputUnavailableError(
                AudioOutput.SONOS, "no speaker is selected"
            )
        return self._client

    async def _replace_client(
        self, client: SonosClient, selected: SonosSpeaker
    ) -> None:
        previous = self._client
        self._stopped.set()
        try:
            if previous is not None:
                await previous.stop()
        except BaseException:
            await client.close()
            raise
        self._client = client
        self._selected_speaker = selected
        if previous is not None:
            await previous.close()

    async def _await_end(self, speaker: SonosClient, stopped: asyncio.Event) -> None:
        """Return once the speaker stopped, so ``play`` outlasts the sound."""
        while not stopped.is_set():
            await asyncio.sleep(_POLL_INTERVAL)
            info = await speaker.get_transport_info()
            if info.state is None or info.state not in _PLAYING_STATES:
                return


def _speaker_id(speaker: Speaker) -> str:
    return speaker.uid or speaker.ip


def _speaker_from_system(speaker: Speaker, system: SonosSystem) -> SonosSpeaker:
    group = next(
        (candidate for candidate in system.groups if speaker in candidate.members), None
    )
    return SonosSpeaker(
        id=_speaker_id(speaker),
        name=speaker.room_name,
        ip_address=speaker.ip,
        group_id=group.id if group is not None else None,
        is_coordinator=speaker.is_coordinator,
    )


def _speakers_from_system(system: SonosSystem) -> tuple[SonosSpeaker, ...]:
    return tuple(_speaker_from_system(speaker, system) for speaker in system.speakers)


@asynccontextmanager
async def _translated_errors() -> AsyncGenerator[None]:
    """Speaker trouble is an unavailable output, not a bug in the caller."""
    from sonosify import SonosifyError

    try:
        yield
    except SonosifyError as error:
        raise AudioOutputUnavailableError(AudioOutput.SONOS, str(error)) from error
