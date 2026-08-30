from types import SimpleNamespace
from unittest.mock import AsyncMock

from huerise.features.lighting.domain import HueBridge
from huerise.features.lighting.infrastructure.hue import HueifyOnboarding


async def test_maps_hueify_discovery_to_domain_bridges(monkeypatch) -> None:
    discover = AsyncMock(
        return_value=[SimpleNamespace(id="bridge-1", internalipaddress="10.0.0.2")]
    )
    monkeypatch.setattr(
        "huerise.features.lighting.infrastructure.hue.discover_bridges", discover
    )

    bridges = await HueifyOnboarding().discover()

    assert bridges == (HueBridge("bridge-1", "10.0.0.2"),)


async def test_registers_a_named_huerise_device(monkeypatch) -> None:
    register = AsyncMock(return_value="secret")
    monkeypatch.setattr(
        "huerise.features.lighting.infrastructure.hue.register_app_key", register
    )

    app_key = await HueifyOnboarding().register("10.0.0.2")

    assert app_key == "secret"
    register.assert_awaited_once_with("10.0.0.2", device_type="huerise#backend")
