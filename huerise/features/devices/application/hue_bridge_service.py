from dataclasses import dataclass
from enum import StrEnum

from huerise.features.devices.application.ports import (
    HueConfigurator,
    HueEnvironmentOverride,
    HueOnboarding,
)
from huerise.features.devices.domain import (
    HueBridge,
    HueBridgeNotFoundError,
    HueBridgeNotSelectedError,
    HueBridgeRepository,
    HueBridgeSelection,
    HueDiscoveryError,
    HueEnvironmentOverrideError,
    HueLinkButtonTimeoutError,
    HueRegistrationError,
)


class HueConfigurationSource(StrEnum):
    ENVIRONMENT = "environment"
    DATABASE = "database"


@dataclass(frozen=True, slots=True)
class HueBridgeStatus:
    bridge_id: str | None
    ip_address: str | None
    configured: bool
    source: HueConfigurationSource | None


@dataclass(frozen=True, slots=True)
class DiscoveredHueBridge:
    bridge: HueBridge
    selected: bool


class HueBridgeService:
    def __init__(
        self,
        repository: HueBridgeRepository,
        connection: HueConfigurator,
        environment: HueEnvironmentOverride,
        onboarding: HueOnboarding,
    ) -> None:
        self._repository = repository
        self._connection = connection
        self._environment = environment
        self._onboarding = onboarding

    async def status(self) -> HueBridgeStatus:
        if self._environment.configured:
            return HueBridgeStatus(
                bridge_id=None,
                ip_address=self._environment.bridge_ip,
                configured=True,
                source=HueConfigurationSource.ENVIRONMENT,
            )
        selected = await self._repository.get_selected()
        if selected is None:
            return HueBridgeStatus(None, None, False, None)
        return HueBridgeStatus(
            bridge_id=selected.bridge_id,
            ip_address=selected.ip_address,
            configured=selected.configured,
            source=HueConfigurationSource.DATABASE,
        )

    async def discover(self) -> tuple[DiscoveredHueBridge, ...]:
        try:
            found = await self._onboarding.discover()
        except Exception as error:
            raise HueDiscoveryError() from error
        status = await self.status()
        return tuple(
            DiscoveredHueBridge(
                bridge=bridge,
                selected=(
                    bridge.id == status.bridge_id
                    if status.bridge_id is not None
                    else bridge.ip_address == status.ip_address
                ),
            )
            for bridge in found
        )

    async def select(self, bridge_id: str) -> HueBridgeStatus:
        self._ensure_database_controlled()
        bridges = [item.bridge for item in await self.discover()]
        bridge = next((item for item in bridges if item.id == bridge_id), None)
        if bridge is None:
            raise HueBridgeNotFoundError(bridge_id)

        previous = await self._repository.get_selected()
        app_key = (
            previous.app_key
            if previous is not None and previous.bridge_id == bridge.id
            else None
        )
        selected = await self._repository.save_selected(
            HueBridgeSelection(bridge.id, bridge.ip_address, app_key)
        )
        if selected.configured:
            await self._connection.configure(selected)
        return await self.status()

    async def register(self) -> HueBridgeStatus:
        self._ensure_database_controlled()
        selected = await self._repository.get_selected()
        if selected is None:
            raise HueBridgeNotSelectedError()
        try:
            app_key = await self._onboarding.register(selected.ip_address)
        except TimeoutError as error:
            raise HueLinkButtonTimeoutError() from error
        except Exception as error:
            raise HueRegistrationError("Could not register with Hue Bridge") from error
        configured = await self._repository.save_selected(
            HueBridgeSelection(
                selected.bridge_id,
                selected.ip_address,
                app_key,
            )
        )
        await self._connection.configure(configured)
        return await self.status()

    def _ensure_database_controlled(self) -> None:
        if self._environment.configured:
            raise HueEnvironmentOverrideError()
