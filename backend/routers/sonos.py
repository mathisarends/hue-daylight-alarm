from fastapi import APIRouter

from backend.src.infrastructure.audio.strategies.sonos import (
    SonosDevice,
    discover_sonos_devices,
)

router = APIRouter(prefix="/sonos", tags=["Sonos"])


@router.get("/devices", response_model=list[SonosDevice])
def list_sonos_devices(timeout: int = 5) -> list[SonosDevice]:
    return discover_sonos_devices(timeout=timeout)
