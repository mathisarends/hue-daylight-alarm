from contextlib import suppress
from uuid import UUID

from huerise.features.daylight_alarm.service import DaylightAlarm
from huerise.features.lighting.hue import (
    HueClientFactory,
    HueCredentialsProvider,
    HueUnavailableError,
    Room,
)


class SceneService:
    def __init__(
        self,
        credentials: HueCredentialsProvider,
        clients: HueClientFactory,
        alarm: DaylightAlarm,
    ) -> None:
        self._credentials = credentials
        self._clients = clients
        self._alarm = alarm

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

    async def demo(self, room_id: UUID, scene_id: UUID) -> None:
        await self._alarm.demo(room_id, scene_id)

    async def stop_demo(self) -> None:
        await self._alarm.stop()
