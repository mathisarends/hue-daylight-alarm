from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import Field, IPvAnyAddress, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="HUERISE_",
        extra="ignore",
    )

    api_key: SecretStr
    config_path: Path = Path("huerise.yml")
    log_level: LogLevel = LogLevel.INFO


class HueEnvironment(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_prefix="HUE_",
        extra="ignore",
    )

    bridge_ip: IPvAnyAddress | None = None
    app_key: SecretStr | None = Field(default=None, min_length=20)

    @model_validator(mode="after")
    def require_complete_pair(self) -> Self:
        if (self.bridge_ip is None) != (self.app_key is None):
            raise ValueError(
                "HUE_BRIDGE_IP and HUE_APP_KEY must either both be set or both be unset"
            )
        return self

    @property
    def configured(self) -> bool:
        return self.bridge_ip is not None and self.app_key is not None
