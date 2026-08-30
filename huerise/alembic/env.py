import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel
from sqlmodel.sql.sqltypes import AutoString

from huerise.infrastructure.database.models import (
    AlarmModel,
    AlarmOccurrenceModel,
    AlarmProfileModel,
    HueBridgeSelectionModel,
    RefreshTokenModel,
    UserModel,
)
from huerise.infrastructure.database.types import UtcDateTime

__all__ = [
    "AlarmModel",
    "AlarmOccurrenceModel",
    "AlarmProfileModel",
    "HueBridgeSelectionModel",
    "RefreshTokenModel",
    "UserModel",
]

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

db_url = os.environ.get("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

target_metadata = SQLModel.metadata


def render_item(type_: str, obj: object, autogen_context: object) -> str | bool:
    """Keep generated migrations free of application imports.

    Autogenerate would otherwise spell columns as ``sqlmodel.sql.sqltypes.
    AutoString()`` or ``huerise.infrastructure.database.types.UtcDateTime()``
    without emitting the imports, so the revision fails at import time -- and
    would pin the migration to code that is free to move.
    """
    if type_ != "type":
        return False
    if isinstance(obj, UtcDateTime):
        return "sa.DateTime(timezone=True)"
    if isinstance(obj, AutoString):
        return "sa.String()"
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        render_item=render_item,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
