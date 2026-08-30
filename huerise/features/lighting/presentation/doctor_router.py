from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.authentication import require_api_key
from huerise.features.lighting.application import Doctor
from huerise.features.lighting.presentation.schemas import DoctorResponse

doctor_router = APIRouter(
    tags=["health"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@doctor_router.get(
    "/doctor",
    response_model=DoctorResponse,
    operation_id="doctor",
)
async def doctor(service: FromDishka[Doctor]) -> DoctorResponse:
    return DoctorResponse.from_report(await service.check())
