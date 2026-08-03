import logging

from huerise.features.devices.application.ports import Lights
from huerise.features.devices.domain import (
    Room,
    RoomNotFoundError,
    SceneNotFoundError,
)

logger = logging.getLogger(__name__)


class SceneService:
    """Browsing and previewing what an alarm can be pointed at."""

    def __init__(self, lights: Lights) -> None:
        self._lights = lights

    async def list_rooms(self) -> list[Room]:
        return await self._lights.list_rooms()

    async def get_room(self, room_name: str) -> Room:
        room = next(
            (r for r in await self._lights.list_rooms() if r.name == room_name),
            None,
        )
        if room is None:
            raise RoomNotFoundError(room_name)
        return room

    async def activate_scene(self, room_name: str, scene_name: str) -> None:
        """Preview a scene the way an alarm would start it."""
        room = await self.get_room(room_name)
        if scene_name not in room.scene_names:
            raise SceneNotFoundError(room_name, scene_name)

        logger.info("Activating scene '%s' in room '%s'", scene_name, room_name)
        await self._lights.activate_scene(room_name, scene_name)
