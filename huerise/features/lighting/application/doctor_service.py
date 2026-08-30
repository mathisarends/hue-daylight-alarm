from dataclasses import dataclass

from huerise.features.lighting.application.hue_bridge_service import HueBridgeService


@dataclass(frozen=True, slots=True)
class SetupCheck:
    configured: bool


@dataclass(frozen=True, slots=True)
class DoctorStatus:
    hue_bridge: SetupCheck

    @property
    def configured(self) -> bool:
        return self.hue_bridge.configured


class DoctorService:
    def __init__(self, hue: HueBridgeService) -> None:
        self._hue = hue

    async def check(self) -> DoctorStatus:
        hue = await self._hue.status()
        return DoctorStatus(hue_bridge=SetupCheck(configured=hue.configured))
