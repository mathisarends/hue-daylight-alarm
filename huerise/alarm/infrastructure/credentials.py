from pydantic_settings import BaseSettings, SettingsConfigDict


class HueCredentials(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="HUE_",
    )

    app_key: str
    bridge_ip: str


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    database_url: str = "sqlite+aiosqlite:///./data/daylight.db"

    @property
    def async_url(self) -> str:
        """Ensure the URL uses an async driver (aiosqlite for SQLite)."""
        if (
            self.database_url.startswith("sqlite:///")
            and "+aiosqlite" not in self.database_url
        ):
            return self.database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return self.database_url
