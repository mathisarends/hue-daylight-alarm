from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.features.devices.application import DoctorService
from huerise.features.devices.presentation.doctor_schemas import DoctorRead
from huerise.presentation import require_access_token

doctor_router = APIRouter(
    tags=["health"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_access_token)],
)


@doctor_router.get("/doctor", response_model=DoctorRead, operation_id="doctor")
async def doctor(service: FromDishka[DoctorService]) -> DoctorRead:
    return DoctorRead.from_domain(await service.check())
