from pathlib import Path

import pytest

from huerise.configuration import YamlConfiguration
from huerise.env import HueEnvironment
from huerise.features.lighting.application import (
    BridgeNotFoundError,
    BridgeNotSelectedError,
    HueBridge,
    HueOnboarding,
    HueUnavailableError,
    LinkButtonTimeoutError,
    OnboardingReadOnlyError,
    OnboardingState,
)
from tests.huerise.features.lighting.fakes import FakeOnboardingGateway

BRIDGES = (
    HueBridge("bridge-1", "192.0.2.10"),
    HueBridge("bridge-2", "192.0.2.11"),
)


def make_onboarding(
    tmp_path: Path, gateway: FakeOnboardingGateway | None = None
) -> HueOnboarding:
    return HueOnboarding(
        YamlConfiguration(tmp_path / "huerise.yml"),
        HueEnvironment(_env_file=None),
        gateway or FakeOnboardingGateway(BRIDGES),
    )


async def test_exposes_client_friendly_onboarding_states(tmp_path: Path) -> None:
    onboarding = make_onboarding(tmp_path)
    assert onboarding.status().state is OnboardingState.NOT_SELECTED

    selected = await onboarding.select("bridge-2")
    assert selected.state is OnboardingState.LINK_BUTTON_REQUIRED
    assert selected.bridge_id == "bridge-2"

    registered = await onboarding.register()
    assert registered.state is OnboardingState.READY
    assert registered.ip_address == "192.0.2.11"


async def test_discovery_marks_the_selected_bridge(tmp_path: Path) -> None:
    onboarding = make_onboarding(tmp_path)
    await onboarding.select("bridge-2")

    bridges = await onboarding.discover()

    assert [bridge.selected for bridge in bridges] == [False, True]


async def test_rejects_unknown_bridge(tmp_path: Path) -> None:
    with pytest.raises(BridgeNotFoundError):
        await make_onboarding(tmp_path).select("missing")


async def test_requires_selection_before_registration(tmp_path: Path) -> None:
    with pytest.raises(BridgeNotSelectedError):
        await make_onboarding(tmp_path).register()


async def test_keeps_selection_after_link_button_timeout(tmp_path: Path) -> None:
    onboarding = make_onboarding(
        tmp_path,
        FakeOnboardingGateway(BRIDGES, registration_error=TimeoutError()),
    )
    await onboarding.select("bridge-2")

    with pytest.raises(LinkButtonTimeoutError):
        await onboarding.register()

    assert onboarding.status().state is OnboardingState.LINK_BUTTON_REQUIRED


async def test_environment_configuration_is_ready_and_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HUE_BRIDGE_IP", "192.0.2.20")
    monkeypatch.setenv("HUE_APP_KEY", "environment-hue-key-123")
    onboarding = HueOnboarding(
        YamlConfiguration(tmp_path / "huerise.yml"),
        HueEnvironment(_env_file=None),
        FakeOnboardingGateway(BRIDGES),
    )

    status = onboarding.status()
    assert status.state is OnboardingState.READY
    assert status.read_only is True
    with pytest.raises(OnboardingReadOnlyError):
        await onboarding.select("bridge-1")


async def test_reports_discovery_failures(tmp_path: Path) -> None:
    onboarding = make_onboarding(
        tmp_path,
        FakeOnboardingGateway(discovery_error=OSError("discovery offline")),
    )

    with pytest.raises(HueUnavailableError, match="Could not discover Hue Bridges"):
        await onboarding.discover()


async def test_reports_registration_failures(tmp_path: Path) -> None:
    onboarding = make_onboarding(
        tmp_path,
        FakeOnboardingGateway(BRIDGES, registration_error=OSError("offline")),
    )
    await onboarding.select("bridge-2")

    with pytest.raises(HueUnavailableError, match="Could not register with Hue Bridge"):
        await onboarding.register()

    assert onboarding.status().state is OnboardingState.LINK_BUTTON_REQUIRED
