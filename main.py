import logging
from dataclasses import dataclass

from soco import SoCo
from soco.discovery import discover

logger = logging.getLogger("daylight_alarm.sonos_discovery")


@dataclass
class SonosDevice:
    ip_address: str
    name: str
    model: str


def discover_all(timeout: int = 5) -> list[SonosDevice]:
    devices = discover(timeout=timeout)

    if not devices:
        logger.warning("No Sonos devices found")
        return []

    logger.info(f"Found {len(devices)} device(s)")

    return [_extract_info(device) for device in devices]


def _extract_info(device: SoCo) -> SonosDevice:
    info = device.get_speaker_info()

    return SonosDevice(
        ip_address=device.ip_address,
        name=info.get("zone_name", "Unknown"),
        model=info.get("model_name", "Unknown"),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    devices = discover_all()
    for dev in devices:
        print(f"Name: {dev.name}, IP: {dev.ip_address}, Model: {dev.model}")
