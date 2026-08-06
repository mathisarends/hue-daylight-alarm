from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from huerise.features.devices.application.hue_bridge_service import HueBridgeService
from huerise.features.devices.domain import (
    HueBridge,
    HueBridgeNotFoundError,
    HueBridgeSelection,
    HueEnvironmentOverrideError,
)


def make_service(selected=None, *, environment=False):
    state = [selected]
    repository = MagicMock()
    repository.get_selected = AsyncMock(side_effect=lambda: state[0])

    async def save(item):
        state[0] = item
        return item

    repository.save_selected = AsyncMock(side_effect=save)
    connection = MagicMock()
    connection.configure = AsyncMock()
    override = SimpleNamespace(
        configured=environment,
        bridge_ip="192.168.1.99" if environment else None,
    )
    onboarding = MagicMock()
    onboarding.discover = AsyncMock(return_value=())
    onboarding.register = AsyncMock()
    service = HueBridgeService(repository, connection, override, onboarding)
    return service, repository, connection, onboarding


async def test_selects_a_discovered_bridge_without_fabricating_credentials(
    monkeypatch,
) -> None:
    service, repository, connection, onboarding = make_service()
    onboarding.discover.return_value = (HueBridge("bridge-1", "10.0.0.2"),)

    status = await service.select("bridge-1")

    assert status.configured is False
    repository.save_selected.assert_awaited_once_with(
        HueBridgeSelection("bridge-1", "10.0.0.2", None)
    )
    connection.configure.assert_not_awaited()


async def test_rejects_an_unknown_bridge(monkeypatch) -> None:
    service, _, _, _ = make_service()

    with pytest.raises(HueBridgeNotFoundError):
        await service.select("missing")


async def test_registration_persists_key_and_reconfigures_runtime(monkeypatch) -> None:
    selected = HueBridgeSelection("bridge-1", "10.0.0.2")
    service, repository, connection, onboarding = make_service(selected)
    onboarding.register.return_value = "new-secret"

    status = await service.register()

    configured = HueBridgeSelection("bridge-1", "10.0.0.2", "new-secret")
    repository.save_selected.assert_awaited_once_with(configured)
    connection.configure.assert_awaited_once_with(configured)
    assert status.configured is True
    onboarding.register.assert_awaited_once_with("10.0.0.2")


async def test_environment_override_prevents_database_selection() -> None:
    service, _, _, _ = make_service(environment=True)

    with pytest.raises(HueEnvironmentOverrideError):
        await service.select("bridge-1")
