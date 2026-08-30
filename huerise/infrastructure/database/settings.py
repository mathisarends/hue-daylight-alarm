from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://huerise:huerise@localhost:5432/huerise"
    )

    @property
    def async_url(self) -> str:
        """Ensure the URL uses the async driver.

        Postgres tooling and connection strings from hosting providers almost
        always spell the scheme ``postgres://`` or ``postgresql://``, which
        SQLAlchemy resolves to the synchronous psycopg driver.
        """
        database_url = self.database_url.get_secret_value()
        scheme, separator, rest = database_url.partition("://")
        if not separator or "+" in scheme:
            return database_url
        if scheme in ("postgres", "postgresql"):
            return f"postgresql+asyncpg://{rest}"
        return database_url
