from unittest.mock import AsyncMock, MagicMock

from huerise.features.devices.application import DoctorService, HueBridgeStatus


async def test_reports_configured_when_hue_bridge_is_configured() -> None:
    hue = MagicMock()
    hue.status = AsyncMock(
        return_value=HueBridgeStatus(None, None, configured=True, source=None)
    )

    status = await DoctorService(hue).check()

    assert status.hue_bridge.configured is True
    assert status.configured is True


async def test_reports_not_configured_when_hue_bridge_is_not_configured() -> None:
    hue = MagicMock()
    hue.status = AsyncMock(
        return_value=HueBridgeStatus(None, None, configured=False, source=None)
    )

    status = await DoctorService(hue).check()

    assert status.hue_bridge.configured is False
    assert status.configured is False
