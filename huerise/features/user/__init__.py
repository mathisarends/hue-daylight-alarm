from huerise.presentation import Feature

from .infrastructure.di import UserProvider

feature = Feature(
    name="user",
    providers=[UserProvider],
)

__all__ = ["feature"]
