from dataclasses import dataclass

from huerise.features.devices.application.audio_output import SwitchableAudioPlayer
from huerise.features.devices.application.ports import SonosSpeakerSelector
from huerise.features.devices.domain import (
    AudioOutput,
    AudioOutputUnavailableError,
    SonosSpeaker,
    SonosSpeakerRepository,
)


@dataclass(frozen=True, slots=True)
class SonosSpeakerStatus:
    speaker: SonosSpeaker
    selected: bool


class SonosSpeakerService:
    def __init__(
        self,
        audio: SwitchableAudioPlayer,
        sonos_speaker_repository: SonosSpeakerRepository,
    ) -> None:
        self._audio = audio
        self._sonos_speaker_repository = sonos_speaker_repository

    async def discover(self) -> tuple[SonosSpeakerStatus, ...]:
        selector = self._selector()
        speakers = await selector.discover_speakers()
        selected = selector.selected_speaker
        return tuple(
            SonosSpeakerStatus(
                speaker=speaker,
                selected=selected is not None and speaker.id == selected.id,
            )
            for speaker in speakers
        )

    async def select(self, speaker_id: str) -> SonosSpeakerStatus:
        speaker = await self._selector().select_speaker(speaker_id)
        await self._sonos_speaker_repository.save_selected(speaker)
        return SonosSpeakerStatus(speaker=speaker, selected=True)

    def _selector(self) -> SonosSpeakerSelector:
        player = self._audio.player_for(AudioOutput.SONOS)
        if not isinstance(player, SonosSpeakerSelector):
            raise AudioOutputUnavailableError(
                AudioOutput.SONOS, "the configured player cannot select speakers"
            )
        return player
