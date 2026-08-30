from huerise.presentation import Feature

from .infrastructure import LightingProvider
from .presentation import (
    doctor_router,
    hue_router,
    register_lighting_exception_handlers,
    scene_router,
)

feature = Feature(
    name="lighting",
    routers=[
        scene_router,
        hue_router,
        doctor_router,
    ],
    providers=[LightingProvider],
    register_exception_handlers=register_lighting_exception_handlers,
)

__all__ = ["feature"]
