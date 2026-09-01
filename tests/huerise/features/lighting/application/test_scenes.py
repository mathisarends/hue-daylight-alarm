from uuid import UUID

import pytest

from huerise.features.lighting.application import (
    HueUnavailableError,
    Room,
    Scene,
    SceneService,
)
from tests.huerise.features.lighting.fakes import (
    FakeHueClient,
    FakeHueClientFactory,
    FakeHueCredentialsSource,
)

SCENE_ID = UUID(int=1)
ROOM_ID = UUID(int=2)


def make_service(
    client: FakeHueClient,
    *,
    credentials: FakeHueCredentialsSource | None = None,
    factory: FakeHueClientFactory | None = None,
) -> SceneService:
    return SceneService(
        credentials or FakeHueCredentialsSource(),
        factory or FakeHueClientFactory(client),
    )


async def test_lists_rooms_with_their_scenes() -> None:
    client = FakeHueClient([Room(ROOM_ID, "Bedroom", (Scene(SCENE_ID, "Sunrise"),))])
    service = make_service(client)

    rooms = await service.list_rooms()

    assert rooms == client.rooms
    assert client.closed is True


async def test_preserves_unavailable_credentials_error() -> None:
    error = HueUnavailableError("not configured")
    service = make_service(
        FakeHueClient(),
        credentials=FakeHueCredentialsSource(error=error),
    )

    with pytest.raises(HueUnavailableError, match="not configured"):
        await service.list_rooms()


async def test_wraps_client_initialization_errors() -> None:
    client = FakeHueClient()
    service = make_service(
        client,
        factory=FakeHueClientFactory(client, error=OSError("bad transport")),
    )

    with pytest.raises(HueUnavailableError, match="initialize Hue Bridge connection"):
        await service.list_rooms()

    assert client.closed is False


async def test_wraps_room_listing_errors_and_still_closes_client() -> None:
    client = FakeHueClient(
        list_rooms_error=OSError("offline"),
        close_error=OSError("already disconnected"),
    )

    with pytest.raises(HueUnavailableError, match="list Hue rooms and scenes"):
        await make_service(client).list_rooms()

    assert client.closed is True
