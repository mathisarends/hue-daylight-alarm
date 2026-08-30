from dataclasses import dataclass
from pathlib import Path

import pytest

from huerise.configuration import HueEnvironment, YamlConfiguration
from huerise.onboarding import (
    BridgeNotFoundError,
    BridgeNotSelectedError,
    HueBridge,
    HueOnboarding,
    LinkButtonTimeoutError,
    OnboardingReadOnlyError,
    OnboardingState,
)


@dataclass
class StubGateway:
    bridges: tuple[HueBridge, ...] = (
        HueBridge("bridge-1", "192.0.2.10"),
        HueBridge("bridge-2", "192.0.2.11"),
    )
    app_key: str = "registered-key"
    registration_error: Exception | None = None

    async def discover(self) -> tuple[HueBridge, ...]:
        return self.bridges

    async def register(self, bridge_ip: str) -> str:
        assert bridge_ip == "192.0.2.11"
        if self.registration_error is not None:
            raise self.registration_error
        return self.app_key


def make_onboarding(
    tmp_path: Path, gateway: StubGateway | None = None
) -> HueOnboarding:
    return HueOnboarding(
        YamlConfiguration(tmp_path / "huerise.yml"),
        HueEnvironment(_env_file=None),
        gateway or StubGateway(),
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
        tmp_path, StubGateway(registration_error=TimeoutError())
    )
    await onboarding.select("bridge-2")

    with pytest.raises(LinkButtonTimeoutError):
        await onboarding.register()

    assert onboarding.status().state is OnboardingState.LINK_BUTTON_REQUIRED


async def test_environment_configuration_is_ready_and_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HUE_BRIDGE_IP", "192.0.2.20")
    monkeypatch.setenv("HUE_APP_KEY", "environment-key")
    onboarding = HueOnboarding(
        YamlConfiguration(tmp_path / "huerise.yml"),
        HueEnvironment(_env_file=None),
        StubGateway(),
    )

    status = onboarding.status()
    assert status.state is OnboardingState.READY
    assert status.read_only is True
    with pytest.raises(OnboardingReadOnlyError):
        await onboarding.select("bridge-1")
