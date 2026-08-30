from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.features.lighting.application import DoctorService
from huerise.features.lighting.presentation.doctor_schemas import DoctorRead
from huerise.presentation import get_current_user

doctor_router = APIRouter(
    tags=["health"],
    route_class=DishkaRoute,
    dependencies=[Depends(get_current_user)],
)


@doctor_router.get("/doctor", response_model=DoctorRead, operation_id="doctor")
async def doctor(service: FromDishka[DoctorService]) -> DoctorRead:
    return DoctorRead.from_domain(await service.check())
