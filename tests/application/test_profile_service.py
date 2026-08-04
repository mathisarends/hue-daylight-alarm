from uuid import uuid4

import pytest

from huerise.features.alarm.application import AlarmProfileService
from huerise.features.alarm.domain import (
    AlarmProfileNotFoundError,
    IntroConfig,
    RingtoneConfig,
    SunriseConfig,
)
from tests.application.conftest import InMemoryProfileRepository, make_profile


async def test_create_profile_defaults_the_sunrise_config() -> None:
    profiles = InMemoryProfileRepository()
    service = AlarmProfileService(profiles)

    profile = await service.create(
        name="Weekday",
        intro_config=IntroConfig(sound_id=uuid4()),
        ringtone_config=RingtoneConfig(sound_id=uuid4()),
    )

    assert profile.name == "Weekday"
    assert profile.sunrise_config == SunriseConfig()
    assert await profiles.find_by_id(profile.id) == profile


async def test_create_profile_keeps_a_given_sunrise_config() -> None:
    service = AlarmProfileService(InMemoryProfileRepository())
    sunrise = SunriseConfig(brightness_start=10)

    profile = await service.create(
        name="Weekday",
        intro_config=IntroConfig(sound_id=uuid4()),
        ringtone_config=RingtoneConfig(sound_id=uuid4()),
        sunrise_config=sunrise,
    )

    assert profile.sunrise_config == sunrise


async def test_find_all_profiles() -> None:
    profile = make_profile()

    result = await AlarmProfileService(InMemoryProfileRepository([profile])).find_all()

    assert result == [profile]


async def test_find_profile_by_id() -> None:
    profile = make_profile()

    result = await AlarmProfileService(InMemoryProfileRepository([profile])).find_by_id(
        profile.id
    )

    assert result == profile


async def test_find_missing_profile() -> None:
    profile_id = uuid4()
    service = AlarmProfileService(InMemoryProfileRepository())

    with pytest.raises(AlarmProfileNotFoundError):
        await service.find_by_id(profile_id)


async def test_delete_profile() -> None:
    profile = make_profile(is_default=False)
    profiles = InMemoryProfileRepository([profile])

    await AlarmProfileService(profiles).delete(profile.id)

    assert await profiles.find_by_id(profile.id) is None


async def test_delete_missing_profile() -> None:
    service = AlarmProfileService(InMemoryProfileRepository())

    with pytest.raises(AlarmProfileNotFoundError):
        await service.delete(uuid4())
