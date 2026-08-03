from huerise.presentation import Feature

from .infrastructure import DevicesProvider
from .presentation import register_device_exception_handlers, sound_router

feature = Feature(
    name="devices",
    routers=[sound_router],
    providers=[DevicesProvider],
    register_exception_handlers=register_device_exception_handlers,
)

__all__ = ["feature"]
