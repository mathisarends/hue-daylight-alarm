from abc import ABC, abstractmethod

from huerise.features.devices.domain.sonos_speaker import SonosSpeaker


class SonosSpeakerRepository(ABC):
    @abstractmethod
    async def get_selected(self) -> SonosSpeaker | None: ...

    @abstractmethod
    async def save_selected(self, speaker: SonosSpeaker) -> SonosSpeaker: ...
