import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from sonosify.models import Group, Speaker

from huerise.features.devices.domain import (
    AudioOutputUnavailableError,
    Sound,
    SoundCategory,
    SoundRepository,
)
from huerise.features.devices.infrastructure import sonos
from huerise.features.devices.infrastructure.settings import SonosSettings
from huerise.features.devices.infrastructure.sonos import SonosAudioPlayer
from huerise.infrastructure.storage import StorageBackend

SOUND_ID = UUID("1693baba-146e-5b14-acf2-6f76554f36e9")


async def make_player(speaker: MagicMock) -> SonosAudioPlayer:
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

    controller = MagicMock()
    controller.client = AsyncMock(return_value=speaker)
    player = SonosAudioPlayer(sounds, storage, controller)
    await player.configure(None, speaker.ip)
    return player


def make_speaker(states: list[str]) -> MagicMock:
    """A speaker reporting ``states`` one poll at a time, then STOPPED."""
    speaker = MagicMock()
    speaker.ip = "192.168.1.42"
    speaker.uid = "RINCON_BEDROOM"
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
    player = await make_player(speaker)

    await player.play(SOUND_ID, volume=40)

    speaker.set_volume.assert_awaited_once_with(40)
    speaker.play_uri.assert_awaited_once_with(
        "http://192.168.1.5:9000/bowls.mp3", title="bowls"
    )


async def test_play_returns_only_once_the_speaker_stopped() -> None:
    speaker = make_speaker(["TRANSITIONING", "PLAYING", "PLAYING"])
    player = await make_player(speaker)

    await player.play(SOUND_ID, volume=40)

    assert speaker.get_transport_info.await_count == 4


async def test_stop_ends_a_running_playback() -> None:
    speaker = make_speaker(["PLAYING"] * 100)
    player = await make_player(speaker)

    playing = asyncio.create_task(player.play(SOUND_ID, volume=40))
    await asyncio.sleep(0)
    await player.stop()

    await asyncio.wait_for(playing, timeout=1)
    speaker.stop.assert_awaited_once()


async def test_stop_is_forwarded_to_the_injected_speaker() -> None:
    speaker = make_speaker([])
    player = await make_player(speaker)

    await player.stop()

    speaker.stop.assert_awaited_once()


async def test_unconfigured_player_starts_without_discovery() -> None:
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
    storage.public_url = AsyncMock(return_value="http://storage/bowls.mp3")
    controller = MagicMock()
    player = SonosAudioPlayer(sounds, storage, controller)

    with pytest.raises(AudioOutputUnavailableError, match="no speaker is selected"):
        await player.play(SOUND_ID, volume=40)

    controller.discover.assert_not_called()


async def test_discovers_and_selects_speaker_by_stable_uid() -> None:
    client = make_speaker([])
    bedroom = Speaker(
        ip="192.168.1.42",
        room_name="Bedroom",
        uid="RINCON_BEDROOM",
        coordinator_uid="RINCON_BEDROOM",
        is_coordinator=True,
    )
    group = Group(id="GROUP_1", coordinator_uid=bedroom.uid, members=(bedroom,))
    system = MagicMock()
    system.speakers = (bedroom,)
    system.groups = (group,)
    system.client.return_value = client
    controller = MagicMock()
    controller.system = None
    controller.discover = AsyncMock(return_value=system)
    sounds = MagicMock(spec=SoundRepository)
    storage = MagicMock(spec=StorageBackend)
    player = SonosAudioPlayer(sounds, storage, controller)

    discovered = await player.discover_speakers()
    controller.system = system
    selected = await player.select_speaker("RINCON_BEDROOM")

    assert discovered == (selected,)
    assert selected.id == "RINCON_BEDROOM"
    assert selected.name == "Bedroom"
    assert selected.group_id == "GROUP_1"
    assert selected.is_coordinator is True
    assert player.selected_speaker == selected
    system.client.assert_called_once_with(ip="192.168.1.42", coordinator=True)


async def test_selecting_another_speaker_stops_and_closes_previous_client() -> None:
    first_client = make_speaker([])
    second_client = make_speaker([])
    first = Speaker(ip="192.168.1.41", room_name="Office", uid="RINCON_OFFICE")
    second = Speaker(ip="192.168.1.42", room_name="Bedroom", uid="RINCON_BEDROOM")
    system = MagicMock()
    system.speakers = (first, second)
    system.groups = ()
    system.client.side_effect = [first_client, second_client]
    controller = MagicMock()
    controller.system = system
    player = SonosAudioPlayer(
        MagicMock(spec=SoundRepository), MagicMock(spec=StorageBackend), controller
    )

    await player.select_speaker(first.uid)
    selected = await player.select_speaker(second.uid)

    assert selected.id == second.uid
    first_client.stop.assert_awaited_once()
    first_client.close.assert_awaited_once()
