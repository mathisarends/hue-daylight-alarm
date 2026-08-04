import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from huerise.features.devices.domain import Sound, SoundCategory, SoundRepository
from huerise.features.devices.infrastructure import sonos
from huerise.features.devices.infrastructure.settings import SonosSettings
from huerise.features.devices.infrastructure.sonos import SonosAudioPlayer
from huerise.infrastructure.storage import StorageBackend

SOUND_ID = UUID("1693baba-146e-5b14-acf2-6f76554f36e9")


def make_player(speaker: MagicMock) -> SonosAudioPlayer:
    sounds = MagicMock(spec=SoundRepository)
    sounds.get = AsyncMock(
        return_value=Sound(
            id=SOUND_ID,
            name="bowls",
            category=SoundCategory.WAKE_UP,
            storage_path="wake_up_sounds/wake-up-bowls.mp3",
        )
    )
    storage = MagicMock(spec=StorageBackend)
    storage.public_url = AsyncMock(return_value="http://192.168.1.5:9000/bowls.mp3")

    return SonosAudioPlayer(sounds, storage, speaker)


def make_speaker(states: list[str]) -> MagicMock:
    """A speaker reporting ``states`` one poll at a time, then STOPPED."""
    speaker = MagicMock()
    speaker.ip = "192.168.1.42"
    speaker.set_volume = AsyncMock()
    speaker.play_uri = AsyncMock()
    speaker.stop = AsyncMock()
    speaker.get_transport_info = AsyncMock(
        side_effect=[MagicMock(state=state) for state in [*states, "STOPPED"]]
    )
    speaker.get_room_name = AsyncMock(return_value="Bedroom")
    speaker.close = AsyncMock()
    return speaker


def test_reads_speaker_name_and_ip_address_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SONOS_SPEAKER_NAME", "Sonos Era 100")
    monkeypatch.setenv("SONOS_IP_ADDRESS", "192.168.178.68")

    settings = SonosSettings(_env_file=None)

    assert settings.speaker_name == "Sonos Era 100"
    assert settings.ip_address == "192.168.178.68"


@pytest.fixture(autouse=True)
def instant_polling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sonos, "_POLL_INTERVAL", 0)


async def test_hands_the_speaker_a_link_instead_of_the_bytes() -> None:
    speaker = make_speaker([])
    player = make_player(speaker)

    await player.play(SOUND_ID, volume=40)

    speaker.set_volume.assert_awaited_once_with(40)
    speaker.play_uri.assert_awaited_once_with(
        "http://192.168.1.5:9000/bowls.mp3", title="bowls"
    )


async def test_play_returns_only_once_the_speaker_stopped() -> None:
    speaker = make_speaker(["TRANSITIONING", "PLAYING", "PLAYING"])
    player = make_player(speaker)

    await player.play(SOUND_ID, volume=40)

    assert speaker.get_transport_info.await_count == 4


async def test_stop_ends_a_running_playback() -> None:
    speaker = make_speaker(["PLAYING"] * 100)
    player = make_player(speaker)

    playing = asyncio.create_task(player.play(SOUND_ID, volume=40))
    await asyncio.sleep(0)
    await player.stop()

    await asyncio.wait_for(playing, timeout=1)
    speaker.stop.assert_awaited_once()


async def test_stop_is_forwarded_to_the_injected_speaker() -> None:
    speaker = make_speaker([])
    player = make_player(speaker)

    await player.stop()

    speaker.stop.assert_awaited_once()
