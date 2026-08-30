from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import Depends, status

from huerise.authentication import require_api_key
from huerise.configuration import ConfigurationError
from huerise.exception_handlers import ExceptionRouter, error
from huerise.features.lighting.application import (
    BridgeNotFoundError,
    BridgeNotSelectedError,
    HueOnboarding,
    HueUnavailableError,
    LinkButtonTimeoutError,
    OnboardingReadOnlyError,
)
from huerise.features.lighting.presentation.mappers import (
    to_bridge_response,
    to_onboarding_status_response,
)
from huerise.features.lighting.presentation.schemas import (
    BridgeResponse,
    BridgeSelectionRequest,
    OnboardingStatusResponse,
)

hue_router = ExceptionRouter(
    prefix="/hue",
    tags=["hue-setup"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@hue_router.get(
    "/bridges",
    response_model=list[BridgeResponse],
    operation_id="listHueBridges",
    errors={
        ConfigurationError: error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "The stored Hue configuration is invalid.",
        ),
        HueUnavailableError: error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Hue Bridge discovery is unavailable.",
        ),
    },
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
    errors={
        ConfigurationError: error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "The stored Hue configuration is invalid.",
        ),
    },
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
    errors={
        BridgeNotFoundError: error(
            status.HTTP_404_NOT_FOUND,
            "The selected Hue Bridge was not discovered.",
        ),
        OnboardingReadOnlyError: error(
            status.HTTP_409_CONFLICT,
            "Environment overrides make Hue onboarding read-only.",
        ),
        ConfigurationError: error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "The stored Hue configuration is invalid.",
        ),
        HueUnavailableError: error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Hue Bridge discovery is unavailable.",
        ),
    },
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
    errors={
        BridgeNotSelectedError: error(
            status.HTTP_409_CONFLICT,
            "A Hue Bridge must be selected before registration.",
        ),
        LinkButtonTimeoutError: error(
            status.HTTP_409_CONFLICT,
            "The Hue Bridge link button was not pressed in time.",
        ),
        OnboardingReadOnlyError: error(
            status.HTTP_409_CONFLICT,
            "Environment overrides make Hue onboarding read-only.",
        ),
        ConfigurationError: error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "The stored Hue configuration is invalid.",
        ),
        HueUnavailableError: error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Hue Bridge registration is unavailable.",
        ),
    },
)
async def register_bridge(
    service: FromDishka[HueOnboarding],
) -> OnboardingStatusResponse:
    status = await service.register()
    return to_onboarding_status_response(status)
