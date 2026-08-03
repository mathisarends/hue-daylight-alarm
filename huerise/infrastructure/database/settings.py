from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    database_url: SecretStr = SecretStr("sqlite+aiosqlite:///./data/daylight.db")

    @property
    def async_url(self) -> str:
        """Ensure the URL uses an async driver (aiosqlite for SQLite)."""
        database_url = self.database_url.get_secret_value()
        if database_url.startswith("sqlite:///") and "+aiosqlite" not in database_url:
            return database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return database_url
