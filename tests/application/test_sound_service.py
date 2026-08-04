import asyncio
import logging
from uuid import UUID

import pytest

from huerise.features.devices.application import SoundService
from huerise.features.devices.domain import SoundNotFoundError
from tests.application.conftest import InMemorySoundRepository, make_audio, make_sounds


def make_sound_service(audio) -> SoundService:
    return SoundService(InMemorySoundRepository(make_sounds()), audio)


class TestSoundService:
    async def test_preview_starts_playback_without_waiting_for_it(self) -> None:
        audio = make_audio()
        service = make_sound_service(audio)

        sound_id = UUID("1693baba-146e-5b14-acf2-6f76554f36e9")
        sound = await service.preview(sound_id, volume=30)
        await asyncio.sleep(0)

        assert sound.id == sound_id
        audio.stop.assert_awaited_once()
        audio.play.assert_awaited_once_with(sound_id, 30)

    async def test_preview_rejects_an_unknown_sound(self) -> None:
        audio = make_audio()
        service = make_sound_service(audio)

        with pytest.raises(SoundNotFoundError):
            await service.preview(UUID("680dc52c-db89-5a81-aaa2-860a89ccef39"))

        audio.play.assert_not_awaited()

    async def test_preview_logs_background_playback_errors(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        audio = make_audio()
        audio.play.side_effect = RuntimeError("speaker is offline")
        service = make_sound_service(audio)
        sound_id = UUID("1693baba-146e-5b14-acf2-6f76554f36e9")

        with caplog.at_level(logging.ERROR):
            await service.preview(sound_id)
            await asyncio.sleep(0)
            await asyncio.sleep(0)

        assert "Sound preview playback failed" in caplog.text
        assert "speaker is offline" in caplog.text
