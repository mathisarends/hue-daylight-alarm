import logging
from datetime import timedelta
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
        intro_audio_file: str,
        ringtone_audio_file: str,
        scene_name: str = "Tageslichtwecker",
        sunrise_duration_minutes: int = 7,
        brightness_start: int = 1,
        brightness_end: int = 100,
        ringtone_volume: int = 80,
    ) -> AlarmProfile:
        logger.info("Creating alarm profile '%s'", name)
        profile = AlarmProfile(
            name=name,
            intro_config=IntroConfig(audio_file=intro_audio_file),
            sunrise_config=SunriseConfig(
                scene_name=scene_name,
                duration=timedelta(minutes=sunrise_duration_minutes),
                brightness_start=brightness_start,
                brightness_end=brightness_end,
            ),
            ringtone_config=RingtoneConfig(
                audio_file=ringtone_audio_file, volume=ringtone_volume
            ),
        )
        return await self._profiles.save(profile)
