from uuid import UUID

from hueify import Hueify

from huerise.features.devices.application import Lights
from huerise.features.devices.domain import Room, Scene


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
                    Scene(id=scene.id, name=scene.name)
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
