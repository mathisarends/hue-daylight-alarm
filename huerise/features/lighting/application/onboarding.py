import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from huerise.configuration import HueConfig, HueEnvironment, YamlConfiguration
from huerise.features.lighting.application.models import HueUnavailableError


class OnboardingState(StrEnum):
    NOT_SELECTED = "not_selected"
    LINK_BUTTON_REQUIRED = "link_button_required"
    READY = "ready"


class OnboardingReadOnlyError(Exception):
    pass


class BridgeNotFoundError(Exception):
    def __init__(self, bridge_id: str) -> None:
        super().__init__(f"Hue Bridge not found: {bridge_id}")


class BridgeNotSelectedError(Exception):
    pass


class LinkButtonTimeoutError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class HueBridge:
    id: str
    ip_address: str


@dataclass(frozen=True, slots=True)
class DiscoveredBridge:
    id: str
    ip_address: str
    selected: bool


@dataclass(frozen=True, slots=True)
class OnboardingStatus:
    state: OnboardingState
    bridge_id: str | None
    ip_address: str | None
    read_only: bool


class OnboardingGateway(Protocol):
    async def discover(self) -> tuple[HueBridge, ...]: ...

    async def register(self, bridge_ip: str) -> str: ...


class HueOnboarding:
    def __init__(
        self,
        configuration: YamlConfiguration,
        environment: HueEnvironment,
        gateway: OnboardingGateway,
    ) -> None:
        self._configuration = configuration
        self._environment = environment
        self._gateway = gateway
        self._lock = asyncio.Lock()

    def status(self) -> OnboardingStatus:
        if self._environment.configured:
            assert self._environment.bridge_ip is not None
            return OnboardingStatus(
                state=OnboardingState.READY,
                bridge_id=None,
                ip_address=str(self._environment.bridge_ip),
                read_only=True,
            )

        hue = self._configuration.load_hue()
        if hue is None:
            return OnboardingStatus(
                state=OnboardingState.NOT_SELECTED,
                bridge_id=None,
                ip_address=None,
                read_only=False,
            )
        return OnboardingStatus(
            state=(
                OnboardingState.READY
                if hue.app_key is not None
                else OnboardingState.LINK_BUTTON_REQUIRED
            ),
            bridge_id=hue.bridge_id,
            ip_address=str(hue.bridge_ip),
            read_only=False,
        )

    async def discover(self) -> tuple[DiscoveredBridge, ...]:
        try:
            bridges = await self._gateway.discover()
        except Exception as error:
            raise HueUnavailableError("Could not discover Hue Bridges") from error
        selected = self.status()
        return tuple(
            DiscoveredBridge(
                id=bridge.id,
                ip_address=bridge.ip_address,
                selected=(
                    bridge.id == selected.bridge_id
                    if selected.bridge_id is not None
                    else bridge.ip_address == selected.ip_address
                ),
            )
            for bridge in bridges
        )

    async def select(self, bridge_id: str) -> OnboardingStatus:
        self._ensure_writable()
        async with self._lock:
            bridges = await self.discover()
            bridge = next((item for item in bridges if item.id == bridge_id), None)
            if bridge is None:
                raise BridgeNotFoundError(bridge_id)
            self._configuration.save_hue(
                HueConfig(bridge_id=bridge.id, bridge_ip=bridge.ip_address)
            )
            return self.status()

    async def register(self) -> OnboardingStatus:
        self._ensure_writable()
        async with self._lock:
            hue = self._configuration.load_hue()
            if hue is None:
                raise BridgeNotSelectedError("Select a Hue Bridge before registering")
            try:
                app_key = await self._gateway.register(str(hue.bridge_ip))
            except TimeoutError as error:
                raise LinkButtonTimeoutError(
                    "Hue Bridge link button was not pressed in time"
                ) from error
            except Exception as error:
                raise HueUnavailableError(
                    "Could not register with Hue Bridge"
                ) from error
            self._configuration.save_hue(
                HueConfig(
                    bridge_id=hue.bridge_id,
                    bridge_ip=hue.bridge_ip,
                    app_key=app_key,
                )
            )
            return self.status()

    def _ensure_writable(self) -> None:
        if self._environment.configured:
            raise OnboardingReadOnlyError(
                "Hue onboarding is read-only while environment overrides are set"
            )
