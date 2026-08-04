from huerise.infrastructure.database.settings import DatabaseSettings


def test_adds_the_async_driver_to_a_plain_sqlite_url() -> None:
    settings = DatabaseSettings(
        database_url="sqlite:///./data/daylight.db", _env_file=None
    )

    assert settings.async_url == "sqlite+aiosqlite:///./data/daylight.db"


def test_leaves_an_already_async_sqlite_url_alone() -> None:
    settings = DatabaseSettings(
        database_url="sqlite+aiosqlite:///./data/daylight.db", _env_file=None
    )

    assert settings.async_url == "sqlite+aiosqlite:///./data/daylight.db"


def test_leaves_a_non_sqlite_url_alone() -> None:
    settings = DatabaseSettings(
        database_url="postgresql+asyncpg://user:pass@host/db", _env_file=None
    )

    assert settings.async_url == "postgresql+asyncpg://user:pass@host/db"
