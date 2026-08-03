import pytest

from huerise.features.devices.application import SoundCatalog
from huerise.features.devices.domain import SoundCategory, SoundNotFoundError
from tests.application.conftest import make_sound_storage


class TestSoundCatalog:
    async def test_lists_every_category_by_default(self) -> None:
        catalog = SoundCatalog(make_sound_storage())

        assert [sound.id for sound in await catalog.list_sounds()] == [
            "get_up/aurora",
            "wake_up/bowls",
            "wake_up/mist",
        ]

    async def test_filters_by_category(self) -> None:
        catalog = SoundCatalog(make_sound_storage())

        sounds = await catalog.list_sounds(SoundCategory.GET_UP)

        assert [sound.id for sound in sounds] == ["get_up/aurora"]

    async def test_serves_repeated_lookups_from_the_cache(self) -> None:
        storage = make_sound_storage()
        catalog = SoundCatalog(storage)

        await catalog.get("wake_up/bowls")
        await catalog.get("wake_up/mist")

        assert storage.list_calls == len(SoundCategory)

    async def test_refreshes_once_before_giving_up_on_an_unknown_id(self) -> None:
        storage = make_sound_storage()
        catalog = SoundCatalog(storage)
        await catalog.list_sounds()

        storage.paths.append("wake_up_sounds/wake-up-gong.mp3")

        assert (await catalog.get("wake_up/gong")).name == "gong"

    async def test_rejects_an_id_that_does_not_exist(self) -> None:
        catalog = SoundCatalog(make_sound_storage())

        with pytest.raises(SoundNotFoundError):
            await catalog.get("wake_up/nope")
