from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HueBridge:
    id: str
    ip_address: str


@dataclass(frozen=True, slots=True)
class HueBridgeSelection:
    bridge_id: str
    ip_address: str
    app_key: str | None = None

    @property
    def configured(self) -> bool:
        return self.app_key is not None
