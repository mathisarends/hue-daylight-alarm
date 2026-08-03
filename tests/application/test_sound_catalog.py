from uuid import UUID

import pytest

from huerise.features.devices.application import SoundCatalog
from huerise.features.devices.domain import SoundCategory, SoundNotFoundError
from tests.application.conftest import make_sound_storage


class TestSoundCatalog:
    async def test_lists_every_category_by_default(self) -> None:
        catalog = SoundCatalog(make_sound_storage())

        assert [sound.id for sound in await catalog.list_sounds()] == [
            UUID("5c0806e7-7162-5be7-948e-33d349bde4a8"),
            UUID("1693baba-146e-5b14-acf2-6f76554f36e9"),
            UUID("bb804011-6bb8-5b4e-9d90-ebe5e11becb0"),
        ]

    async def test_filters_by_category(self) -> None:
        catalog = SoundCatalog(make_sound_storage())

        sounds = await catalog.list_sounds(SoundCategory.GET_UP)

        assert [sound.id for sound in sounds] == [
            UUID("5c0806e7-7162-5be7-948e-33d349bde4a8")
        ]

    async def test_serves_repeated_lookups_from_the_cache(self) -> None:
        storage = make_sound_storage()
        catalog = SoundCatalog(storage)

        await catalog.get(UUID("1693baba-146e-5b14-acf2-6f76554f36e9"))
        await catalog.get(UUID("bb804011-6bb8-5b4e-9d90-ebe5e11becb0"))

        assert storage.list_calls == len(SoundCategory)

    async def test_refreshes_once_before_giving_up_on_an_unknown_id(self) -> None:
        storage = make_sound_storage()
        catalog = SoundCatalog(storage)
        await catalog.list_sounds()

        storage.paths.append("wake_up_sounds/wake-up-gong.mp3")

        assert (
            await catalog.get(UUID("4b8afa3c-8898-5b5c-833b-4171ceacc90c"))
        ).name == "gong"

    async def test_rejects_an_id_that_does_not_exist(self) -> None:
        catalog = SoundCatalog(make_sound_storage())

        with pytest.raises(SoundNotFoundError):
            await catalog.get(UUID("680dc52c-db89-5a81-aaa2-860a89ccef39"))
