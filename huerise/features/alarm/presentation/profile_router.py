from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.features.alarm.application import AlarmProfileService
from huerise.features.alarm.presentation.profile_schemas import (
    ProfileCreate,
    ProfileRead,
)
from huerise.presentation import require_access_token

profile_router = APIRouter(
    prefix="/alarm-profiles",
    tags=["Alarm Profiles"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_access_token)],
)


@profile_router.get("", response_model=list[ProfileRead], operation_id="listProfiles")
async def list_profiles(
    profile_service: FromDishka[AlarmProfileService],
) -> list[ProfileRead]:
    profiles = await profile_service.list_profiles()
    return [ProfileRead.from_domain(profile) for profile in profiles]


@profile_router.post(
    "", response_model=ProfileRead, status_code=201, operation_id="createProfile"
)
async def create_profile(
    body: ProfileCreate,
    profile_service: FromDishka[AlarmProfileService],
) -> ProfileRead:
    profile = await profile_service.create_profile(
        name=body.name,
        intro_config=body.intro.to_domain(),
        sunrise_config=body.sunrise.to_domain(),
        ringtone_config=body.ringtone.to_domain(),
    )
    return ProfileRead.from_domain(profile)
