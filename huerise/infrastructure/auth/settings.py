from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AUTH_",
        extra="ignore",
    )

    jwt_secret: SecretStr
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
