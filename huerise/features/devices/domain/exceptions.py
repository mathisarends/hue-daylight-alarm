class DeviceError(Exception):
    """Base for everything the devices feature raises."""


class SoundNotFoundError(DeviceError):
    def __init__(self, sound_id: str) -> None:
        super().__init__(f"Sound {sound_id} not found")
