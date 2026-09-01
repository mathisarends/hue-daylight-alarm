from huerise.shared import Feature

from .infrastructure import LightingProvider
from .presentation import doctor_router, hue_router

feature = Feature(
    name="lighting",
    routers=[doctor_router, hue_router],
    providers=[LightingProvider],
)
