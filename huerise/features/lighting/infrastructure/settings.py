from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from huerise.features.lighting.application.ports import HueEnvironmentOverride


class HueEnvironment(BaseSettings, HueEnvironmentOverride):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="HUE_",
        extra="ignore",
    )

    app_key: SecretStr | None = None
    bridge_ip: str | None = None

    @model_validator(mode="after")
    def require_complete_pair(self):
        if (self.app_key is None) != (self.bridge_ip is None):
            raise ValueError(
                "HUE_BRIDGE_IP and HUE_APP_KEY must either both be set or both be unset"
            )
        return self

    @property
    def configured(self) -> bool:
        return self.app_key is not None and self.bridge_ip is not None
