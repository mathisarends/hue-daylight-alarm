import asyncio
import logging
from typing import ClassVar
from uuid import UUID

from hueify import Hueify
from hueify.models import ResourceType, RoomEvent, SceneEvent
from hueify.models import Scene as HueScene
from hueify.onboarding import discover_bridges, register_app_key

from huerise.features.devices.application import (
    LightChangeHandler,
    LightEvents,
    Lights,
)
from huerise.features.devices.application.ports import HueConfigurator, HueOnboarding
from huerise.features.devices.domain import (
    HueBridge,
    HueBridgeRepository,
    HueBridgeSelection,
    HueUnavailableError,
    LightChange,
    LightResource,
    Room,
    Scene,
)
from huerise.features.devices.infrastructure.settings import HueEnvironment

logger = logging.getLogger(__name__)


class HueifyOnboarding(HueOnboarding):
    async def discover(self) -> tuple[HueBridge, ...]:
        return tuple(
            HueBridge(item.id, item.internalipaddress)
            for item in await discover_bridges()
        )

    async def register(self, bridge_ip: str) -> str:
        return await register_app_key(bridge_ip, device_type="huerise#backend")


class ConfigurableHue(Lights, LightEvents, HueConfigurator):
    """A Hue runtime that can exist before onboarding has supplied credentials."""

    def __init__(
        self,
        repository: HueBridgeRepository,
        environment: HueEnvironment,
        onboarding: HueOnboarding,
    ) -> None:
        self._repository = repository
        self._environment = environment
        self._onboarding = onboarding
        self._client: Hueify | None = None
        self._lights: HueLights | None = None
        self._events: HueLightEvents | None = None
        self._handlers: list[LightChangeHandler] = []
        self._started = False
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._started = True
        selection = await self._effective_selection()
        if selection is not None:
            await self.configure(selection)

    async def stop(self) -> None:
        self._started = False
        async with self._lock:
            await self._close()

    def subscribe(self, handler: LightChangeHandler) -> None:
        if handler not in self._handlers:
            self._handlers.append(handler)
        if self._events is not None:
            self._events.subscribe(handler)

    def unsubscribe(self, handler: LightChangeHandler) -> None:
        if handler in self._handlers:
            self._handlers.remove(handler)
        if self._events is not None:
            self._events.unsubscribe(handler)

    async def configure(self, selection: HueBridgeSelection) -> None:
        if selection.app_key is None:
            raise HueUnavailableError("Philips Hue Bridge is not registered")
        async with self._lock:
            await self._close()
            client = Hueify(selection.ip_address, selection.app_key)
            events = HueLightEvents(client)
            for handler in self._handlers:
                events.subscribe(handler)
            self._client = client
            self._lights = HueLights(client)
            self._events = events
            if self._started:
                await events.start()

    async def list_rooms(self) -> list[Room]:
        return await self._require_lights().list_rooms()

    async def activate_scene(
        self, scene_id: UUID, *, brightness: float | None = None
    ) -> None:
        await self._require_lights().activate_scene(scene_id, brightness=brightness)

    async def set_brightness(self, room_id: UUID, brightness: float) -> None:
        await self._require_lights().set_brightness(room_id, brightness)

    def _require_lights(self) -> HueLights:
        if self._lights is None:
            raise HueUnavailableError("Philips Hue Bridge is not configured")
        return self._lights

    async def _effective_selection(self) -> HueBridgeSelection | None:
        if self._environment.configured:
            assert self._environment.bridge_ip is not None
            assert self._environment.app_key is not None
            return HueBridgeSelection(
                bridge_id="environment",
                ip_address=self._environment.bridge_ip,
                app_key=self._environment.app_key.get_secret_value(),
            )
        selected = await self._repository.get_selected()
        if selected is None or not selected.configured:
            return None
        try:
            bridges = await self._onboarding.discover()
            resolved = next(
                (
                    item.ip_address
                    for item in bridges
                    if item.id == selected.bridge_id
                ),
                selected.ip_address,
            )
        except Exception:
            logger.warning(
                "Could not refresh the address of Hue Bridge %s; using %s",
                selected.bridge_id,
                selected.ip_address,
                exc_info=True,
            )
            resolved = selected.ip_address
        if resolved != selected.ip_address:
            selected = await self._repository.save_selected(
                HueBridgeSelection(selected.bridge_id, resolved, selected.app_key)
            )
        return selected

    async def _close(self) -> None:
        client, self._client = self._client, None
        self._lights = None
        self._events = None
        if client is not None:
            await client.close()


class HueLights(Lights):
    def __init__(self, hue: Hueify) -> None:
        self._hue = hue

    async def list_rooms(self) -> list[Room]:
        rooms = (await self._hue.rooms.list()).data
        return [
            Room(
                id=room.id,
                name=room.name,
                scenes=tuple(
                    Scene(
                        id=scene.id,
                        name=scene.name,
                        brightness=_scene_brightness(scene),
                    )
                    for scene in await self._hue.rooms.scenes(room.id)
                ),
            )
            for room in rooms
        ]

    async def activate_scene(
        self, scene_id: UUID, *, brightness: float | None = None
    ) -> None:
        await self._hue.scenes.activate(scene_id, brightness=brightness)

    async def set_brightness(self, room_id: UUID, brightness: float) -> None:
        await self._hue.rooms.set_brightness(room_id, brightness)


class HueLightEvents(LightEvents):
    _RESOURCES: ClassVar[dict[ResourceType, LightResource]] = {
        ResourceType.ROOM: LightResource.ROOM,
        ResourceType.SCENE: LightResource.SCENE,
    }

    def __init__(self, hue: Hueify) -> None:
        self._hue = hue
        self._handlers: list[LightChangeHandler] = []

    def subscribe(self, handler: LightChangeHandler) -> None:
        self._handlers.append(handler)

    def unsubscribe(self, handler: LightChangeHandler) -> None:
        if handler in self._handlers:
            self._handlers.remove(handler)

    async def start(self) -> None:
        for resource_type in self._RESOURCES:
            self._hue.on(resource_type, self._on_event)
        try:
            await self._hue.start_events()
        except BaseException:
            for resource_type in self._RESOURCES:
                self._hue.off(resource_type, self._on_event)
            raise

    async def stop(self) -> None:
        for resource_type in self._RESOURCES:
            self._hue.off(resource_type, self._on_event)
        await self._hue.stop_events()

    async def _on_event(self, event: RoomEvent | SceneEvent) -> None:
        # Too chatty for INFO: every scene recall passes through here as well.
        logger.debug("Raw Hue event: %s", event.model_dump(exclude_none=True))

        change = LightChange(
            resource=self._RESOURCES[event.type],
            id=event.id,
            name=event.metadata.name if event.metadata else None,
        )
        for handler in self._handlers:
            await handler(change)


def _scene_brightness(scene: HueScene) -> float | None:
    """Return Hue's effective group brightness for a stored scene.

    Hue stores one action per light, not a single scene-level brightness.  The
    grouped-light API represents the group brightness as the mean of its lit
    members, so use the same aggregation here.  Off lights are excluded: their
    remembered dimming value is not part of the visible scene.
    """
    brightnesses: list[float] = []
    for target in scene.actions:
        action = target.action
        if action.is_on is False:
            continue
        brightness = action.brightness
        if brightness is not None:
            brightnesses.append(brightness)

    if not brightnesses:
        return None
    return sum(brightnesses) / len(brightnesses)
