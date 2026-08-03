import asyncio

import pytest

from huerise.features.devices.application import SoundCatalog, SoundService
from huerise.features.devices.domain import SoundNotFoundError
from tests.application.conftest import make_audio, make_sound_storage


def make_sound_service(audio) -> SoundService:
    return SoundService(SoundCatalog(make_sound_storage()), audio)


class TestSoundService:
    async def test_preview_starts_playback_without_waiting_for_it(self) -> None:
        audio = make_audio()
        service = make_sound_service(audio)

        sound = await service.preview("wake_up/bowls", volume=30)
        await asyncio.sleep(0)

        assert sound.id == "wake_up/bowls"
        audio.stop.assert_awaited_once()
        audio.play.assert_awaited_once_with("wake_up/bowls", 30)

    async def test_preview_rejects_an_unknown_sound(self) -> None:
        audio = make_audio()
        service = make_sound_service(audio)

        with pytest.raises(SoundNotFoundError):
            await service.preview("wake_up/nope")

        audio.play.assert_not_awaited()
