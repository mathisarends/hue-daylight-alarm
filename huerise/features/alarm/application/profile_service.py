import logging
from uuid import UUID

from huerise.features.alarm.domain import (
    AlarmProfile,
    AlarmProfileNotFoundError,
    AlarmProfileRepository,
    IntroConfig,
    RingtoneConfig,
    SunriseConfig,
)

logger = logging.getLogger(__name__)


class AlarmProfileService:
    def __init__(self, profiles: AlarmProfileRepository) -> None:
        self._profiles = profiles

    async def list_profiles(self) -> list[AlarmProfile]:
        return await self._profiles.find_all()

    async def get_profile(self, profile_id: UUID) -> AlarmProfile:
        profile = await self._profiles.find_by_id(profile_id)
        if profile is None:
            raise AlarmProfileNotFoundError(profile_id)
        return profile

    async def create_profile(
        self,
        name: str,
        intro_config: IntroConfig,
        ringtone_config: RingtoneConfig,
        sunrise_config: SunriseConfig | None = None,
    ) -> AlarmProfile:
        logger.info("Creating alarm profile '%s'", name)
        profile = AlarmProfile(
            name=name,
            intro_config=intro_config,
            sunrise_config=sunrise_config or SunriseConfig(),
            ringtone_config=ringtone_config,
        )
        return await self._profiles.save(profile)

    async def delete(self, profile_id: UUID) -> None:
        logger.info("Deleting alarm profile %s", profile_id)
        if not await self._profiles.delete_by_id(profile_id):
            raise AlarmProfileNotFoundError(profile_id)
