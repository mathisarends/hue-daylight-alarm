from .doctor_router import doctor_router
from .exception_mappings import (
    register_exception_handlers as register_device_exception_handlers,
)
from .hue_router import hue_router
from .scene_router import scene_router

__all__ = [
    "doctor_router",
    "hue_router",
    "register_device_exception_handlers",
    "scene_router",
]
