from enum import StrEnum


class AudioOutput(StrEnum):
    """Where alarm and preview audio is played."""

    LOCAL = "local"
    SONOS = "sonos"
