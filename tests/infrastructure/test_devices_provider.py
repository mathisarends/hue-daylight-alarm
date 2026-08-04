from unittest.mock import AsyncMock, MagicMock

from dishka import Provider, Scope, make_async_container, provide

from huerise.features.devices.application import SwitchableAudioPlayer
from huerise.features.devices.domain import AudioOutput, SoundRepository
from huerise.features.devices.infrastructure.di import DevicesProvider
from huerise.infrastructure.storage import StorageBackend


class StorageStubProvider(Provider):
    scope = Scope.APP

    @provide
    def storage(self) -> StorageBackend:
        return MagicMock(spec=StorageBackend)

    @provide
    def sounds(self) -> SoundRepository:
        return MagicMock(spec=SoundRepository)


async def test_composition_root_injects_an_eagerly_connected_sonos_client(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AUDIO_BACKENDS", "sonos")
    monkeypatch.delenv("AUDIO_DEFAULT_OUTPUT", raising=False)
    speaker = MagicMock()
    speaker.ip = "192.168.1.42"
    speaker.get_room_name = AsyncMock(return_value="Bedroom")
    speaker.close = AsyncMock()
    controller = MagicMock()
    controller.client = AsyncMock(return_value=speaker)
    controller_type = MagicMock(return_value=controller)
    monkeypatch.setattr("sonosify.SonosController", controller_type)
    container = make_async_container(DevicesProvider(), StorageStubProvider())

    player = await container.get(SwitchableAudioPlayer)

    assert player.active is AudioOutput.SONOS
    assert player.available == (AudioOutput.SONOS,)
    controller_type.assert_called_once()
    controller.client.assert_awaited_once()

    await container.close()
    speaker.close.assert_awaited_once()
