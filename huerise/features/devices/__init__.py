from huerise.presentation import Feature

from .infrastructure import DevicesProvider
from .presentation import (
    audio_output_router,
    register_device_exception_handlers,
    scene_router,
    sound_router,
)

feature = Feature(
    name="devices",
    routers=[sound_router, scene_router, audio_output_router],
    providers=[DevicesProvider],
    register_exception_handlers=register_device_exception_handlers,
)

__all__ = ["feature"]
