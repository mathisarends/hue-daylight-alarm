from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.features.devices.application import SoundService
from huerise.features.devices.domain import SoundCategory
from huerise.features.devices.presentation.schemas import (
    SoundPreviewRequest,
    SoundRead,
    VolumeRequest,
)
from huerise.presentation import require_access_token

sound_router = APIRouter(
    prefix="/sounds",
    tags=["sounds"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_access_token)],
)


@sound_router.get("", response_model=list[SoundRead], operation_id="list_sounds")
async def list_sounds(
    sound_service: FromDishka[SoundService],
    category: SoundCategory | None = None,
) -> list[SoundRead]:
    sounds = await sound_service.find_all(category)
    return [SoundRead.from_domain(sound) for sound in sounds]


@sound_router.post(
    "/preview",
    response_model=SoundRead,
    status_code=202,
    operation_id="preview_sound",
)
async def preview_sound(
    body: SoundPreviewRequest,
    sound_service: FromDishka[SoundService],
) -> SoundRead:
    """Start playback and return immediately -- the sound keeps playing."""
    sound = await sound_service.preview(body.sound_id, volume=body.volume)
    return SoundRead.from_domain(sound)


@sound_router.post(
    "/stop", status_code=204, response_model=None, operation_id="stop_playback"
)
async def stop_playback(sound_service: FromDishka[SoundService]) -> None:
    await sound_service.stop()


@sound_router.post(
    "/volume", status_code=204, response_model=None, operation_id="set_volume"
)
async def set_volume(
    body: VolumeRequest,
    sound_service: FromDishka[SoundService],
) -> None:
    await sound_service.set_volume(body.volume)
