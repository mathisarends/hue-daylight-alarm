from abc import ABC, abstractmethod

from huerise.features.lighting.domain.hue_bridge import HueBridgeSelection


class HueBridgeRepository(ABC):
    @abstractmethod
    async def get_selected(self) -> HueBridgeSelection | None: ...

    @abstractmethod
    async def save_selected(
        self, selection: HueBridgeSelection
    ) -> HueBridgeSelection: ...
