from contextlib import suppress
from dataclasses import dataclass
from typing import Literal, Protocol

from huerise.configuration import HueriseConfig
from huerise.features.lighting.application.models import (
    HueClientFactory,
    HueCredentialsSource,
    HueUnavailableError,
    SceneNotFoundError,
    room_for_scene,
)


class ConfigurationSource(Protocol):
    def load(self) -> HueriseConfig: ...


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
        credentials: HueCredentialsSource,
        clients: HueClientFactory,
    ) -> None:
        self._configuration = configuration
        self._credentials = credentials
        self._clients = clients

    async def check(self) -> DoctorReport:
        config = self._configuration.load()
        credentials = self._credentials.get()
        try:
            client = self._clients.create(credentials)
        except Exception as error:
            raise HueUnavailableError(
                "Could not initialize Hue Bridge connection"
            ) from error
        try:
            rooms = await client.list_rooms()
            room_for_scene(rooms, config.daylight_alarm.scene.id)
        except SceneNotFoundError:
            raise
        except Exception as error:
            raise HueUnavailableError(
                "Could not connect to or authenticate with Hue Bridge"
            ) from error
        finally:
            with suppress(Exception):
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
