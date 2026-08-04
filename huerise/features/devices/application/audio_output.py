import logging
from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from huerise.features.devices.application.ports import AudioPlayer
from huerise.features.devices.domain import AudioOutput, AudioOutputUnavailableError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AudioOutputStatus:
    active: AudioOutput
    available: tuple[AudioOutput, ...]


class SwitchableAudioPlayer(AudioPlayer):
    """Delegates to whichever output is selected, one at a time.

    The runner and the API share this single player, so a switch reaches every
    caller at once -- no re-wiring, and an alarm started before the switch
    keeps running on the device it was started on until it is stopped.
    """

    def __init__(
        self,
        players: Mapping[AudioOutput, AudioPlayer],
        active: AudioOutput,
    ) -> None:
        if active not in players:
            raise AudioOutputUnavailableError(active, "no player is configured for it")
        self._players = dict(players)
        self._active = active

    @property
    def active(self) -> AudioOutput:
        return self._active

    @property
    def available(self) -> tuple[AudioOutput, ...]:
        return tuple(self._players)

    async def select(self, output: AudioOutput) -> None:
        """Stop whatever is playing and route further playback to ``output``."""
        if output not in self._players:
            raise AudioOutputUnavailableError(output, "no player is configured for it")
        if output is self._active:
            return

        await self._current.stop()
        self._active = output
        logger.info("Audio output switched to %s", output)

    async def play(self, sound_id: UUID, volume: int) -> None:
        await self._current.play(sound_id, volume)

    async def stop(self) -> None:
        await self._current.stop()

    async def set_volume(self, volume: int) -> None:
        await self._current.set_volume(volume)

    @property
    def _current(self) -> AudioPlayer:
        return self._players[self._active]


class AudioOutputService:
    def __init__(self, player: SwitchableAudioPlayer) -> None:
        self._player = player

    def status(self) -> AudioOutputStatus:
        return AudioOutputStatus(
            active=self._player.active,
            available=self._player.available,
        )

    async def select(self, output: AudioOutput) -> AudioOutputStatus:
        await self._player.select(output)
        return self.status()
