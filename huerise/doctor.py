from dataclasses import dataclass
from typing import Literal

from huerise.daylight_alarm import ConfigurationSource, CredentialsSource
from huerise.hue import (
    HueClientFactory,
    HueUnavailableError,
    SceneNotFoundError,
    room_for_scene,
)


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    name: str
    status: Literal["ok"] = "ok"


@dataclass(frozen=True, slots=True)
class DoctorReport:
    status: Literal["ok"]
    checks: tuple[DoctorCheck, ...]


class Doctor:
    def __init__(
        self,
        configuration: ConfigurationSource,
        credentials: CredentialsSource,
        clients: HueClientFactory,
    ) -> None:
        self._configuration = configuration
        self._credentials = credentials
        self._clients = clients

    async def check(self) -> DoctorReport:
        config = self._configuration.load()
        credentials = self._credentials.get()
        client = self._clients.create(credentials)
        try:
            rooms = await client.list_rooms()
            room_for_scene(rooms, config.daylight_alarm.scene_id)
        except SceneNotFoundError:
            raise
        except Exception as error:
            raise HueUnavailableError(
                "Could not connect to or authenticate with Hue Bridge"
            ) from error
        finally:
            await client.close()

        return DoctorReport(
            status="ok",
            checks=(
                DoctorCheck("configuration"),
                DoctorCheck("hue_credentials"),
                DoctorCheck("hue_bridge"),
                DoctorCheck("scene"),
            ),
        )
