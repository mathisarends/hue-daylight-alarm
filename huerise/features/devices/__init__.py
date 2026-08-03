from huerise.presentation import Feature

from .infrastructure import DevicesProvider

feature = Feature(name="devices", providers=[DevicesProvider])

__all__ = ["feature"]
