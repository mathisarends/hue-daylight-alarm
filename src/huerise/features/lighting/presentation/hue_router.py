from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import Depends

from huerise.authentication import require_api_key
from huerise.configuration import ConfigurationError
from huerise.exception_handlers import ExceptionRouter
from huerise.features.lighting.application import (
    BridgeNotFoundError,
    BridgeNotSelectedError,
    HueOnboarding,
    HueUnavailableError,
    LinkButtonTimeoutError,
    OnboardingReadOnlyError,
)
from huerise.features.lighting.presentation.errors import (
    hue_bridge_not_selected,
    hue_link_button_timeout,
    hue_onboarding_read_only,
    invalid_stored_hue_configuration,
    selected_hue_bridge_not_found,
    unavailable_hue_discovery,
    unavailable_hue_registration,
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
        ConfigurationError: invalid_stored_hue_configuration,
        HueUnavailableError: unavailable_hue_discovery,
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
    errors={ConfigurationError: invalid_stored_hue_configuration},
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
        BridgeNotFoundError: selected_hue_bridge_not_found,
        OnboardingReadOnlyError: hue_onboarding_read_only,
        ConfigurationError: invalid_stored_hue_configuration,
        HueUnavailableError: unavailable_hue_discovery,
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
        BridgeNotSelectedError: hue_bridge_not_selected,
        LinkButtonTimeoutError: hue_link_button_timeout,
        OnboardingReadOnlyError: hue_onboarding_read_only,
        ConfigurationError: invalid_stored_hue_configuration,
        HueUnavailableError: unavailable_hue_registration,
    },
)
async def register_bridge(
    service: FromDishka[HueOnboarding],
) -> OnboardingStatusResponse:
    status = await service.register()
    return to_onboarding_status_response(status)
