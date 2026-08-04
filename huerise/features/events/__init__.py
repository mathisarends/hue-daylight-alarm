from huerise.presentation import Feature

from .infrastructure import EventsProvider
from .presentation import event_stream_router

feature = Feature(
    name="events",
    routers=[event_stream_router],
    providers=[EventsProvider],
)

__all__ = ["feature"]
