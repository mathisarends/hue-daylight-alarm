from huerise.presentation import Feature

from .provider import LightingProvider
from .router import router

feature = Feature(
    name="lighting",
    routers=[router],
    providers=[LightingProvider],
)
