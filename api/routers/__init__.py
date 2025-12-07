from .alarm import router as alarm_router
from .rooms import router as room_router
from .sounds import router as sound_router

__all__ = ["alarm_router", "room_router", "sound_router"]
