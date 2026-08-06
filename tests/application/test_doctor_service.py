from unittest.mock import AsyncMock, MagicMock

from huerise.features.devices.application import (
    DoctorService,
    HueBridgeStatus,
)


async def test_reports_each_setup_dependency_separately() -> None:
    hue = MagicMock()
    hue.status = AsyncMock(
        return_value=HueBridgeStatus(None, None, configured=True, source=None)
    )
    sonos = MagicMock()
    sonos.get_selected = AsyncMock(return_value=None)

    status = await DoctorService(hue, sonos).check()

    assert status.hue_bridge.configured is True
    assert status.sonos_speaker.configured is False
    assert status.configured is False


async def test_is_configured_when_both_dependencies_are_selected() -> None:
    hue = MagicMock()
    hue.status = AsyncMock(
        return_value=HueBridgeStatus(None, None, configured=True, source=None)
    )
    sonos = MagicMock()
    sonos.get_selected = AsyncMock(return_value=MagicMock())

    status = await DoctorService(hue, sonos).check()

    assert status.configured is True
