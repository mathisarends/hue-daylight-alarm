from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MINIO_",
        extra="ignore",
    )

    endpoint_url: str = "http://localhost:9000"
    access_key: str = "huerise"
    secret_key: str = "huerise-dev-secret"
    bucket_name: str = "huerise-assets"
