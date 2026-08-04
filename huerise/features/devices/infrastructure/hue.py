import logging
from typing import ClassVar
from uuid import UUID

from hueify import Hueify
from hueify.models import ResourceType, RoomEvent, SceneEvent
from hueify.models import Scene as HueScene

from huerise.features.devices.application import (
    LightChangeHandler,
    LightEvents,
    Lights,
)
from huerise.features.devices.domain import LightChange, LightResource, Room, Scene

logger = logging.getLogger(__name__)


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

    async def start(self) -> None:
        for resource_type in self._RESOURCES:
            self._hue.on(resource_type, self._on_event)
        await self._hue.start_events()

    async def _on_event(self, event: RoomEvent | SceneEvent) -> None:
        # The full payload is worth seeing while the shapes of a rename and a
        # deletion are still being pinned down; it is far too chatty for INFO,
        # because every scene recall shows up here too.
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
