from uuid import UUID

from huerise.features.devices.domain.audio_output import AudioOutput


class DeviceError(Exception):
    """Base for everything the devices feature raises."""


class SoundNotFoundError(DeviceError):
    def __init__(self, sound_id: UUID) -> None:
        super().__init__(f"Sound {sound_id} not found")


class RoomNotFoundError(DeviceError):
    def __init__(self, room_id: str) -> None:
        super().__init__(f"Room '{room_id}' not found")


class SceneNotFoundError(DeviceError):
    def __init__(self, room_id: str, scene_id: str) -> None:
        super().__init__(f"Room '{room_id}' has no scene '{scene_id}'")


class AudioOutputUnavailableError(DeviceError):
    """An output was selected or used that cannot be reached right now."""

    def __init__(self, output: AudioOutput, reason: str) -> None:
        self.output = output
        super().__init__(f"Audio output '{output}' is unavailable: {reason}")
