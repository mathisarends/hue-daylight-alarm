from pydantic import BaseModel
from soco import SoCo
from soco.discovery import discover


class SonosDevice(BaseModel):
    ip_address: str
    name: str
    model: str


def discover_sonos_devices(timeout: int = 5) -> list[SonosDevice]:
    devices = discover(timeout=timeout)

    if not devices:
        return []

    return [_extract_info(device) for device in devices]


def _extract_info(device: SoCo) -> SonosDevice:
    info = device.get_speaker_info()

    return SonosDevice(
        ip_address=device.ip_address,
        name=info.get("zone_name", "Unknown"),
        model=info.get("model_name", "Unknown"),
    )
