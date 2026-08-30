from huerise.presentation import Feature

from .infrastructure import DevicesProvider
from .presentation import (
    doctor_router,
    hue_router,
    register_device_exception_handlers,
    scene_router,
)

feature = Feature(
    name="devices",
    routers=[
        scene_router,
        hue_router,
        doctor_router,
    ],
    providers=[DevicesProvider],
    register_exception_handlers=register_device_exception_handlers,
)

__all__ = ["feature"]
