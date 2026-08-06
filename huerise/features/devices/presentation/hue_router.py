from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.features.devices.application import HueBridgeService
from huerise.features.devices.presentation.hue_schemas import (
    HueBridgeRead,
    HueBridgeSelectionRequest,
    HueBridgeStatusRead,
)
from huerise.presentation import require_access_token

hue_router = APIRouter(
    prefix="/hue",
    tags=["hue-setup"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_access_token)],
)

@hue_router.get(
    "/bridges", response_model=list[HueBridgeRead], operation_id="list_hue_bridges"
)
async def list_hue_bridges(
    service: FromDishka[HueBridgeService],
) -> list[HueBridgeRead]:
    bridges = await service.discover()
    return [HueBridgeRead.from_domain(item) for item in bridges]


@hue_router.get(
    "/bridge", response_model=HueBridgeStatusRead, operation_id="get_hue_bridge"
)
async def get_hue_bridge(
    service: FromDishka[HueBridgeService],
) -> HueBridgeStatusRead:
    status = await service.status()
    return HueBridgeStatusRead.from_domain(status)


@hue_router.put(
    "/bridge", response_model=HueBridgeStatusRead, operation_id="select_hue_bridge"
)
async def select_hue_bridge(
    body: HueBridgeSelectionRequest,
    service: FromDishka[HueBridgeService],
) -> HueBridgeStatusRead:
    status = await service.select(body.bridge_id)
    return HueBridgeStatusRead.from_domain(status)


@hue_router.post(
    "/bridge/register",
    response_model=HueBridgeStatusRead,
    operation_id="register_hue_bridge",
)
async def register_hue_bridge(
    service: FromDishka[HueBridgeService],
) -> HueBridgeStatusRead:
    """Wait up to 60 seconds for the selected bridge's link button."""
    status = await service.register()
    return HueBridgeStatusRead.from_domain(status)
