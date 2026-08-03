from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MINIO_",
        extra="ignore",
    )

    endpoint_url: str = "http://localhost:9000"
    public_endpoint_url: str | None = None
    """Endpoint other devices reach the storage under, e.g. ``http://192.168.1.5:9000``.

    A presigned URL is only valid for the host it was signed for, and the
    endpoint this process uses is typically unreachable from a speaker
    elsewhere on the network. Falls back to ``endpoint_url``.
    """

    access_key: SecretStr = SecretStr("huerise")
    secret_key: SecretStr = SecretStr("huerise-dev-secret")
    bucket_name: str = "huerise-assets"
