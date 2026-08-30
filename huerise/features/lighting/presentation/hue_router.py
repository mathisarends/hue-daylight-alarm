from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.authentication import require_api_key
from huerise.features.lighting.application import HueOnboarding
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
    return [BridgeResponse.from_domain(item) for item in await service.discover()]


@hue_router.get(
    "/bridge",
    response_model=OnboardingStatusResponse,
    operation_id="getHueBridge",
)
async def bridge_status(
    service: FromDishka[HueOnboarding],
) -> OnboardingStatusResponse:
    return OnboardingStatusResponse.from_domain(service.status())


@hue_router.put(
    "/bridge",
    response_model=OnboardingStatusResponse,
    operation_id="selectHueBridge",
)
async def select_bridge(
    body: BridgeSelectionRequest,
    service: FromDishka[HueOnboarding],
) -> OnboardingStatusResponse:
    return OnboardingStatusResponse.from_domain(await service.select(body.bridge_id))


@hue_router.post(
    "/bridge/register",
    response_model=OnboardingStatusResponse,
    operation_id="registerHueBridge",
)
async def register_bridge(
    service: FromDishka[HueOnboarding],
) -> OnboardingStatusResponse:
    return OnboardingStatusResponse.from_domain(await service.register())
