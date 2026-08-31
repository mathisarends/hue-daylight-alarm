from .doctor_router import doctor_router
from .hue_router import hue_router
from .scene_router import scene_router
from .schemas import (
    AvailableSceneResponse,
    BridgeResponse,
    BridgeSelectionRequest,
    DoctorCheckResponse,
    DoctorResponse,
    OnboardingStatusResponse,
)

__all__ = [
    "AvailableSceneResponse",
    "BridgeResponse",
    "BridgeSelectionRequest",
    "DoctorCheckResponse",
    "DoctorResponse",
    "OnboardingStatusResponse",
    "doctor_router",
    "hue_router",
    "scene_router",
]
