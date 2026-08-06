from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.features.alarm.application import AlarmProfileService
from huerise.features.alarm.presentation.profile_schemas import (
    ProfileCreate,
    ProfileRead,
)
from huerise.presentation import get_current_user

profile_router = APIRouter(
    prefix="/alarm-profiles",
    tags=["alarm-profiles"],
    route_class=DishkaRoute,
    dependencies=[Depends(get_current_user)],
)


@profile_router.get("", response_model=list[ProfileRead], operation_id="listProfiles")
async def list_profiles(
    profile_service: FromDishka[AlarmProfileService],
) -> list[ProfileRead]:
    profiles = await profile_service.find_all()
    return [ProfileRead.from_domain(profile) for profile in profiles]


@profile_router.post(
    "", response_model=ProfileRead, status_code=201, operation_id="createProfile"
)
async def create_profile(
    body: ProfileCreate,
    profile_service: FromDishka[AlarmProfileService],
) -> ProfileRead:
    profile = await profile_service.create(
        name=body.name,
        intro_config=body.intro.to_domain(),
        sunrise_config=body.sunrise.to_domain(),
        ringtone_config=body.ringtone.to_domain(),
    )
    return ProfileRead.from_domain(profile)


@profile_router.delete(
    "/{profile_id}",
    status_code=204,
    response_model=None,
    operation_id="deleteProfile",
)
async def delete_profile(
    profile_id: UUID,
    profile_service: FromDishka[AlarmProfileService],
) -> None:
    await profile_service.delete(profile_id)
