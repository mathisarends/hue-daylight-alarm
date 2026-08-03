from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

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

    default_output: AudioOutput = AudioOutput.LOCAL
    """Output used until the API switches it -- the switch is not persisted."""


class SonosSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SONOS_",
        extra="ignore",
    )

    room_name: str | None = None
    """Speaker to play on. Without one, discovery picks the first coordinator."""

    ip: str | None = None
    """Skips SSDP discovery, which multicast-blocking networks may swallow."""

    discovery_timeout: float = Field(default=5.0, gt=0)
