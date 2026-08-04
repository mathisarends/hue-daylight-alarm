import logging
from uuid import UUID

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

    async def get_room(self, room_id: UUID) -> Room:
        room = next(
            (r for r in await self._lights.list_rooms() if r.id == room_id),
            None,
        )
        if room is None:
            raise RoomNotFoundError(str(room_id))
        return room

    async def activate_scene(
        self,
        room_id: UUID,
        scene_id: UUID,
        *,
        brightness: float | None = None,
    ) -> None:
        """Preview a scene the way an alarm would start it."""
        room = await self.get_room(room_id)
        scene = next((scene for scene in room.scenes if scene.id == scene_id), None)
        if scene is None:
            raise SceneNotFoundError(str(room_id), str(scene_id))

        logger.info("Activating scene '%s' in room '%s'", scene.name, room.name)
        await self._lights.activate_scene(scene.id, brightness=brightness)
