from typing import Self

from pydantic import BaseModel, Field

from huerise.features.lighting.application import (
    DiscoveredHueBridge,
    HueBridgeStatus,
    HueConfigurationSource,
)


class HueBridgeRead(BaseModel):
    id: str = Field(description="Stable Philips Hue Bridge ID.")
    ip_address: str = Field(description="Current, replaceable network address.")
    selected: bool

    @classmethod
    def from_domain(cls, item: DiscoveredHueBridge) -> Self:
        return cls(
            id=item.bridge.id,
            ip_address=item.bridge.ip_address,
            selected=item.selected,
        )


class HueBridgeSelectionRequest(BaseModel):
    bridge_id: str = Field(min_length=1, description="Stable discovered bridge ID.")


class HueBridgeStatusRead(BaseModel):
    bridge_id: str | None
    ip_address: str | None
    configured: bool
    source: HueConfigurationSource | None

    @classmethod
    def from_domain(cls, status: HueBridgeStatus) -> Self:
        return cls(
            bridge_id=status.bridge_id,
            ip_address=status.ip_address,
            configured=status.configured,
            source=status.source,
        )
