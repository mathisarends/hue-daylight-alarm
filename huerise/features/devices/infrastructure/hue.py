from hueify import Hueify

from huerise.features.devices.application import Lights
from huerise.features.devices.domain import Room


class HueLights(Lights):
    def __init__(self, hue: Hueify) -> None:
        self._hue = hue

    async def list_rooms(self) -> list[Room]:
        rooms = self._hue.rooms
        return [
            Room(name=name, scene_names=tuple(rooms.scene_names(name)))
            for name in rooms.names
        ]

    async def activate_scene(self, room_name: str, scene_name: str) -> None:
        await self._hue.rooms.activate_scene(room_name, scene_name)

    async def set_brightness(self, room_name: str, brightness: int) -> None:
        await self._hue.rooms.set_brightness(room_name, brightness)
