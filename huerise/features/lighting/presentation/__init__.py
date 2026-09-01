from .doctor_router import doctor_router
from .hue_router import hue_router
from .schemas import (
    BridgeResponse,
    BridgeSelectionRequest,
    DoctorCheckResponse,
    DoctorResponse,
    OnboardingStatusResponse,
    RoomResponse,
)

__all__ = [
    "BridgeResponse",
    "BridgeSelectionRequest",
    "DoctorCheckResponse",
    "DoctorResponse",
    "OnboardingStatusResponse",
    "RoomResponse",
    "doctor_router",
    "hue_router",
]
