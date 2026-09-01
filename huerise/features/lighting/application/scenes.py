from contextlib import suppress

from huerise.features.lighting.application.models import (
    HueClientFactory,
    HueCredentialsSource,
    HueUnavailableError,
    Room,
)


class SceneService:
    def __init__(
        self,
        credentials: HueCredentialsSource,
        clients: HueClientFactory,
    ) -> None:
        self._credentials = credentials
        self._clients = clients

    async def list_rooms(self) -> list[Room]:
        try:
            client = self._clients.create(self._credentials.get())
        except HueUnavailableError:
            raise
        except Exception as error:
            raise HueUnavailableError(
                "Could not initialize Hue Bridge connection"
            ) from error
        try:
            return await client.list_rooms()
        except Exception as error:
            raise HueUnavailableError("Could not list Hue rooms and scenes") from error
        finally:
            with suppress(Exception):
                await client.close()
