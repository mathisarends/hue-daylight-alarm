from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.authentication import require_api_key
from huerise.features.lighting.application import HueOnboarding
from huerise.features.lighting.presentation.mappers import (
    to_bridge_response,
    to_onboarding_status_response,
)
from huerise.features.lighting.presentation.schemas import (
    BridgeResponse,
    BridgeSelectionRequest,
    OnboardingStatusResponse,
)

hue_router = APIRouter(
    prefix="/hue",
    tags=["hue-setup"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@hue_router.get(
    "/bridges",
    response_model=list[BridgeResponse],
    operation_id="listHueBridges",
)
async def discover_bridges(
    service: FromDishka[HueOnboarding],
) -> list[BridgeResponse]:
    bridges = await service.discover()
    return [to_bridge_response(bridge) for bridge in bridges]


@hue_router.get(
    "/bridge",
    response_model=OnboardingStatusResponse,
    operation_id="getHueBridge",
)
async def bridge_status(
    service: FromDishka[HueOnboarding],
) -> OnboardingStatusResponse:
    status = service.status()
    return to_onboarding_status_response(status)


@hue_router.put(
    "/bridge",
    response_model=OnboardingStatusResponse,
    operation_id="selectHueBridge",
)
async def select_bridge(
    body: BridgeSelectionRequest,
    service: FromDishka[HueOnboarding],
) -> OnboardingStatusResponse:
    status = await service.select(body.bridge_id)
    return to_onboarding_status_response(status)


@hue_router.post(
    "/bridge/register",
    response_model=OnboardingStatusResponse,
    operation_id="registerHueBridge",
)
async def register_bridge(
    service: FromDishka[HueOnboarding],
) -> OnboardingStatusResponse:
    status = await service.register()
    return to_onboarding_status_response(status)
