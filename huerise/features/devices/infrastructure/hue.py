from hueify import Hueify

from huerise.features.devices.application import Lights


class HueLights(Lights):
    def __init__(self, hue: Hueify) -> None:
        self._hue = hue

    async def activate_scene(self, room_name: str, scene_name: str) -> None:
        await self._hue.rooms.activate_scene(room_name, scene_name)

    async def set_brightness(self, room_name: str, brightness: int) -> None:
        await self._hue.rooms.set_brightness(room_name, brightness)
