from unittest.mock import AsyncMock, MagicMock

import pytest

from huerise.features.devices.application import (
    SonosSpeakerSelector,
    SonosSpeakerService,
    SwitchableAudioPlayer,
)
from huerise.features.devices.domain import (
    AudioOutput,
    AudioOutputUnavailableError,
    SonosSpeaker,
    SonosSpeakerRepository,
)


def make_service(
    *speakers: SonosSpeaker,
) -> tuple[SonosSpeakerService, MagicMock, MagicMock]:
    selector = MagicMock(spec=SonosSpeakerSelector)
    selector.selected_speaker = None
    selector.discover_speakers = AsyncMock(return_value=speakers)
    selector.select_speaker = AsyncMock()
    repository = MagicMock(spec=SonosSpeakerRepository)
    repository.save_selected = AsyncMock()
    audio = SwitchableAudioPlayer(
        {AudioOutput.SONOS: selector}, active=AudioOutput.SONOS
    )
    return SonosSpeakerService(audio, repository), selector, repository


async def test_discovery_marks_the_currently_selected_speaker() -> None:
    office = SonosSpeaker("RINCON_OFFICE", "Office", "192.168.1.41")
    bedroom = SonosSpeaker("RINCON_BEDROOM", "Bedroom", "192.168.1.42")
    service, selector, _ = make_service(office, bedroom)
    selector.selected_speaker = bedroom

    discovered = await service.discover()

    assert [status.selected for status in discovered] == [False, True]


async def test_select_persists_the_connected_speaker() -> None:
    bedroom = SonosSpeaker("RINCON_BEDROOM", "Bedroom", "192.168.1.42")
    service, selector, repository = make_service(bedroom)
    selector.select_speaker.return_value = bedroom

    selected = await service.select(bedroom.id)

    assert selected.speaker == bedroom
    assert selected.selected is True
    repository.save_selected.assert_awaited_once_with(bedroom)


async def test_sonos_selection_is_unavailable_for_local_only_audio() -> None:
    local = MagicMock()
    audio = SwitchableAudioPlayer({AudioOutput.LOCAL: local}, AudioOutput.LOCAL)
    repository = MagicMock(spec=SonosSpeakerRepository)
    service = SonosSpeakerService(audio, repository)

    with pytest.raises(AudioOutputUnavailableError, match="no player is configured"):
        await service.discover()
