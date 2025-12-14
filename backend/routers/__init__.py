from .alarm import router as alarm_router
from .rooms import router as room_router
from .sounds import router as sound_router

from fastapi import APIRouter


api_v1 = APIRouter(prefix="/api/v1", tags=["API v1"])
api_v1.include_router(alarm_router)
api_v1.include_router(room_router)
api_v1.include_router(sound_router)

__all__ = ["api_v1"]
