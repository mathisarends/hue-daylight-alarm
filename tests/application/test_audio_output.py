from uuid import UUID

import pytest

from huerise.features.devices.application import (
    AudioOutputService,
    SwitchableAudioPlayer,
)
from huerise.features.devices.domain import AudioOutput, AudioOutputUnavailableError
from tests.application.conftest import make_audio

SOUND_ID = UUID("1693baba-146e-5b14-acf2-6f76554f36e9")


def make_switchable(
    active: AudioOutput = AudioOutput.LOCAL,
) -> tuple[SwitchableAudioPlayer, dict[AudioOutput, object]]:
    players = {AudioOutput.LOCAL: make_audio(), AudioOutput.SONOS: make_audio()}
    return SwitchableAudioPlayer(players, active=active), players


class TestSwitchableAudioPlayer:
    async def test_plays_on_the_active_output_only(self) -> None:
        player, players = make_switchable()

        await player.play(SOUND_ID, 40)

        players[AudioOutput.LOCAL].play.assert_awaited_once_with(SOUND_ID, 40)
        players[AudioOutput.SONOS].play.assert_not_awaited()

    async def test_select_moves_playback_to_the_other_output(self) -> None:
        player, players = make_switchable()

        await player.select(AudioOutput.SONOS)
        await player.play(SOUND_ID, 40)

        assert player.active is AudioOutput.SONOS
        players[AudioOutput.SONOS].play.assert_awaited_once_with(SOUND_ID, 40)

    async def test_select_stops_the_output_it_leaves(self) -> None:
        player, players = make_switchable()

        await player.select(AudioOutput.SONOS)

        players[AudioOutput.LOCAL].stop.assert_awaited_once()

    async def test_selecting_the_active_output_leaves_playback_alone(self) -> None:
        player, players = make_switchable()

        await player.select(AudioOutput.LOCAL)

        players[AudioOutput.LOCAL].stop.assert_not_awaited()

    async def test_rejects_an_output_without_a_player(self) -> None:
        player = SwitchableAudioPlayer(
            {AudioOutput.LOCAL: make_audio()}, active=AudioOutput.LOCAL
        )

        with pytest.raises(
            AudioOutputUnavailableError,
            match="Audio output 'sonos' is unavailable: no player is configured",
        ):
            await player.select(AudioOutput.SONOS)

    def test_rejects_starting_on_an_output_without_a_player(self) -> None:
        with pytest.raises(AudioOutputUnavailableError):
            SwitchableAudioPlayer(
                {AudioOutput.LOCAL: make_audio()}, active=AudioOutput.SONOS
            )


class TestAudioOutputService:
    def test_reports_the_active_output_and_the_alternatives(self) -> None:
        player, _ = make_switchable()

        status = AudioOutputService(player).status()

        assert status.active is AudioOutput.LOCAL
        assert set(status.available) == {AudioOutput.LOCAL, AudioOutput.SONOS}

    async def test_select_returns_the_switched_status(self) -> None:
        player, _ = make_switchable()

        status = await AudioOutputService(player).select(AudioOutput.SONOS)

        assert status.active is AudioOutput.SONOS
