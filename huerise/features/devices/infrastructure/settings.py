from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from huerise.features.devices.domain import AudioOutput


class HueCredentials(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="HUE_",
        extra="ignore",
    )

    app_key: SecretStr
    bridge_ip: str


class AudioSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AUDIO_",
        extra="ignore",
    )

    backends: Annotated[tuple[AudioOutput, ...], NoDecode] = (AudioOutput.LOCAL,)
    """Backends constructed by the composition root: local, sonos, or all."""

    default_output: AudioOutput | None = None
    """Initially active output. A single configured backend selects itself."""

    @field_validator("backends", mode="before")
    @classmethod
    def parse_backends(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        if value.strip().lower() == "all":
            return (AudioOutput.LOCAL, AudioOutput.SONOS)
        return (value.strip(),) if value.strip() else ()

    @field_validator("backends")
    @classmethod
    def require_backends(
        cls, value: tuple[AudioOutput, ...]
    ) -> tuple[AudioOutput, ...]:
        if not value:
            raise ValueError("configure at least one audio backend")
        return tuple(dict.fromkeys(value))

    @property
    def initial_output(self) -> AudioOutput:
        return self.default_output or self.backends[0]


class SonosSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SONOS_",
        extra="ignore",
    )

    speaker_name: str | None = None
    """Speaker to play on. Without one, discovery picks the first coordinator."""

    ip_address: str | None = None
    """Skips SSDP discovery, which multicast-blocking networks may swallow."""

    discovery_timeout: float = Field(default=5.0, gt=0)
