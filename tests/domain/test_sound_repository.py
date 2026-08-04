from uuid import UUID

import pytest

from huerise.features.devices.domain import SoundNotFoundError
from tests.application.conftest import InMemorySoundRepository, make_sounds


async def test_get_returns_the_sound() -> None:
    sounds = InMemorySoundRepository(make_sounds())

    sound = await sounds.get(UUID("1693baba-146e-5b14-acf2-6f76554f36e9"))

    assert sound.name == "bowls"


async def test_get_rejects_an_unknown_id() -> None:
    sounds = InMemorySoundRepository()

    with pytest.raises(SoundNotFoundError):
        await sounds.get(UUID("680dc52c-db89-5a81-aaa2-860a89ccef39"))
