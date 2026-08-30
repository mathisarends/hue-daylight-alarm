from huerise.features.lighting.application import (
    AvailableScene,
    DiscoveredBridge,
    DoctorReport,
    OnboardingStatus,
    Room,
)
from huerise.features.lighting.presentation.schemas import (
    AvailableSceneResponse,
    BridgeResponse,
    DoctorCheckResponse,
    DoctorResponse,
    OnboardingStatusResponse,
    RoomResponse,
    SceneResponse,
)


def to_doctor_response(report: DoctorReport) -> DoctorResponse:
    return DoctorResponse(
        status=report.status,
        checks=[
            DoctorCheckResponse(name=check.name, status=check.status)
            for check in report.checks
        ],
    )


def to_available_scene_response(scene: AvailableScene) -> AvailableSceneResponse:
    return AvailableSceneResponse(
        id=scene.id,
        name=scene.name,
        room_id=scene.room_id,
        room_name=scene.room_name,
    )


def to_room_response(room: Room) -> RoomResponse:
    return RoomResponse(
        id=room.id,
        name=room.name,
        scenes=[SceneResponse(id=scene.id, name=scene.name) for scene in room.scenes],
    )


def to_bridge_response(bridge: DiscoveredBridge) -> BridgeResponse:
    return BridgeResponse(
        id=bridge.id,
        ip_address=bridge.ip_address,
        selected=bridge.selected,
    )


def to_onboarding_status_response(
    onboarding: OnboardingStatus,
) -> OnboardingStatusResponse:
    return OnboardingStatusResponse(
        state=onboarding.state,
        bridge_id=onboarding.bridge_id,
        ip_address=onboarding.ip_address,
        read_only=onboarding.read_only,
    )
