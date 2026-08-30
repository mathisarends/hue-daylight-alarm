from huerise.infrastructure.database.settings import DatabaseSettings


def test_adds_the_async_driver_to_a_plain_postgres_url() -> None:
    settings = DatabaseSettings(
        database_url="postgresql://user:pass@host/db", _env_file=None
    )

    assert settings.async_url == "postgresql+asyncpg://user:pass@host/db"


def test_adds_the_async_driver_to_the_short_postgres_scheme() -> None:
    settings = DatabaseSettings(
        database_url="postgres://user:pass@host/db", _env_file=None
    )

    assert settings.async_url == "postgresql+asyncpg://user:pass@host/db"


def test_leaves_an_already_async_url_alone() -> None:
    settings = DatabaseSettings(
        database_url="postgresql+asyncpg://user:pass@host/db", _env_file=None
    )

    assert settings.async_url == "postgresql+asyncpg://user:pass@host/db"


def test_leaves_an_explicit_sync_driver_alone() -> None:
    settings = DatabaseSettings(
        database_url="postgresql+psycopg://user:pass@host/db", _env_file=None
    )

    assert settings.async_url == "postgresql+psycopg://user:pass@host/db"
