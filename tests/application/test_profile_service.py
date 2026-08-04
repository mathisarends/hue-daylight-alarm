from uuid import uuid4

import pytest

from huerise.features.alarm.application import AlarmProfileService
from huerise.features.alarm.domain import AlarmProfileNotFoundError
from tests.application.conftest import InMemoryProfileRepository, make_profile


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
