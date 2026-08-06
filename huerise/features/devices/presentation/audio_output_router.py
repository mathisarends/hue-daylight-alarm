from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.features.devices.application import AudioOutputService, SonosSpeakerService
from huerise.features.devices.presentation.schemas import (
    AudioOutputRead,
    AudioOutputRequest,
    SonosSpeakerRead,
    SonosSpeakerRequest,
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


@audio_output_router.get(
    "/sonos/speakers",
    response_model=list[SonosSpeakerRead],
    operation_id="list_sonos_speakers",
)
async def list_sonos_speakers(
    sonos_speaker_service: FromDishka[SonosSpeakerService],
) -> list[SonosSpeakerRead]:
    speakers = await sonos_speaker_service.discover()
    return [SonosSpeakerRead.from_domain(speaker) for speaker in speakers]


@audio_output_router.put(
    "/sonos/speaker",
    response_model=SonosSpeakerRead,
    operation_id="select_sonos_speaker",
)
async def select_sonos_speaker(
    body: SonosSpeakerRequest,
    sonos_speaker_service: FromDishka[SonosSpeakerService],
) -> SonosSpeakerRead:
    selected = await sonos_speaker_service.select(body.speaker_id)
    return SonosSpeakerRead.from_domain(selected)
