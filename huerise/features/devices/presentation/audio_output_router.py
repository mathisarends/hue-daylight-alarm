from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.features.devices.application import AudioOutputService
from huerise.features.devices.presentation.schemas import (
    AudioOutputRead,
    AudioOutputRequest,
)
from huerise.presentation import require_access_token

audio_output_router = APIRouter(
    prefix="/audio-output",
    tags=["audio-output"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_access_token)],
)


@audio_output_router.get(
    "", response_model=AudioOutputRead, operation_id="get_audio_output"
)
async def get_audio_output(
    audio_output_service: FromDishka[AudioOutputService],
) -> AudioOutputRead:
    return AudioOutputRead.from_domain(audio_output_service.status())


@audio_output_router.put(
    "", response_model=AudioOutputRead, operation_id="select_audio_output"
)
async def select_audio_output(
    body: AudioOutputRequest,
    audio_output_service: FromDishka[AudioOutputService],
) -> AudioOutputRead:
    """Switch the output. Anything currently playing is stopped first."""
    status = await audio_output_service.select(body.output)
    return AudioOutputRead.from_domain(status)
