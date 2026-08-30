import logging
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from huerise.features.lighting.application.ports import Lights
from huerise.features.lighting.application.sunrise_demo import SunriseDemoRunner
from huerise.features.lighting.domain import (
    Room,
    RoomNotFoundError,
    Scene,
    SceneNotFoundError,
    SunriseRamp,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SunriseDemo:
    """The ramp a caller just set running, so a client can mirror it."""

    room: Room
    scene: Scene
    ramp: SunriseRamp
    steps: int
    step_interval: timedelta

    @property
    def duration(self) -> timedelta:
        return self.steps * self.step_interval


class SceneService:
    """Browsing and previewing what an alarm can be pointed at."""

    def __init__(self, lights: Lights, demo: SunriseDemoRunner) -> None:
        self._lights = lights
        self._demo = demo

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
        room, scene = await self._get_scene(room_id, scene_id)

        logger.info("Activating scene '%s' in room '%s'", scene.name, room.name)
        await self._lights.activate_scene(scene.id, brightness=brightness)

    async def start_demo(
        self, room_id: UUID, scene_id: UUID, ramp: SunriseRamp
    ) -> SunriseDemo:
        """Run a whole sunrise on this scene in seconds, and report the plan.

        The scene need not belong to a saved alarm -- this is what a user gets
        while still choosing which lights to wake up to.
        """
        room, scene = await self._get_scene(room_id, scene_id)

        logger.info("Demoing a sunrise on '%s' in room '%s'", scene.name, room.name)
        steps = await self._demo.start(room.id, scene.id, ramp)
        return SunriseDemo(
            room=room,
            scene=scene,
            ramp=ramp,
            steps=steps,
            step_interval=self._demo.step_interval,
        )

    async def stop_demo(self) -> None:
        """Cut a running demo short, leaving the lights where it got to."""
        await self._demo.stop()

    async def _get_scene(self, room_id: UUID, scene_id: UUID) -> tuple[Room, Scene]:
        room = await self.get_room(room_id)
        scene = next((scene for scene in room.scenes if scene.id == scene_id), None)
        if scene is None:
            raise SceneNotFoundError(str(room_id), str(scene_id))
        return room, scene
