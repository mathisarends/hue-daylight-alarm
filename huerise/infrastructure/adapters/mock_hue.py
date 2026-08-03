from huerise.application.alarm_service import Lights


class MockHueLights(Lights):
    async def activate_scene(self, room_name: str, scene_name: str) -> None:
        print(f"[MockHue] activate_scene({room_name!r}, {scene_name!r})")

    async def set_brightness(self, room_name: str, brightness: int) -> None:
        print(f"[MockHue] set_brightness({room_name!r}, {brightness})")
