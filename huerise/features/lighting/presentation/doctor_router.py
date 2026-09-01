from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import Depends

from huerise.authentication import require_api_key
from huerise.exception_handlers import ExceptionRouter
from huerise.features.lighting.application import Doctor
from huerise.features.lighting.presentation.errors import doctor_errors
from huerise.features.lighting.presentation.mappers import to_doctor_response
from huerise.features.lighting.presentation.schemas import DoctorResponse

doctor_router = ExceptionRouter(
    tags=["doctor"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@doctor_router.get(
    "/doctor",
    response_model=DoctorResponse,
    operation_id="doctor",
    errors=doctor_errors,
)
async def doctor(
    service: FromDishka[Doctor],
) -> DoctorResponse:
    report = await service.check()
    return to_doctor_response(report)
