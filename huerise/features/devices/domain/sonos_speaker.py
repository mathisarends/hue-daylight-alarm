from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SonosSpeaker:
    id: str
    name: str
    ip_address: str
    group_id: str | None = None
    is_coordinator: bool = False
