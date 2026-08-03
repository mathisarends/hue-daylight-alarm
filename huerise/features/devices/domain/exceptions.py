from uuid import UUID


class DeviceError(Exception):
    """Base for everything the devices feature raises."""


class SoundNotFoundError(DeviceError):
    def __init__(self, sound_id: UUID) -> None:
        super().__init__(f"Sound {sound_id} not found")


class RoomNotFoundError(DeviceError):
    def __init__(self, room_name: str) -> None:
        super().__init__(f"Room '{room_name}' not found")


class SceneNotFoundError(DeviceError):
    def __init__(self, room_name: str, scene_name: str) -> None:
        super().__init__(f"Room '{room_name}' has no scene '{scene_name}'")
