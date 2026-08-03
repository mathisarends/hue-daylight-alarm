from enum import Enum


class SoundCategory(str, Enum):
    GET_UP = "get_up"
    WAKE_UP = "wake_up"

    def __str__(self) -> str:
        return str(self.value)
