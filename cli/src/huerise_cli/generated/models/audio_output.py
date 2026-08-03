from enum import Enum


class AudioOutput(str, Enum):
    LOCAL = "local"
    SONOS = "sonos"

    def __str__(self) -> str:
        return str(self.value)
