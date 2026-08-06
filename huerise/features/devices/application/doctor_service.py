from dataclasses import dataclass

from huerise.features.devices.application.hue_bridge_service import HueBridgeService
from huerise.features.devices.domain import SonosSpeakerRepository


@dataclass(frozen=True, slots=True)
class SetupCheck:
    configured: bool


@dataclass(frozen=True, slots=True)
class DoctorStatus:
    sonos_speaker: SetupCheck
    hue_bridge: SetupCheck

    @property
    def configured(self) -> bool:
        return self.sonos_speaker.configured and self.hue_bridge.configured


class DoctorService:
    def __init__(
        self,
        hue: HueBridgeService,
        sonos_speakers: SonosSpeakerRepository,
    ) -> None:
        self._hue = hue
        self._sonos_speakers = sonos_speakers

    async def check(self) -> DoctorStatus:
        hue = await self._hue.status()
        sonos = await self._sonos_speakers.get_selected()
        return DoctorStatus(
            sonos_speaker=SetupCheck(configured=sonos is not None),
            hue_bridge=SetupCheck(configured=hue.configured),
        )
