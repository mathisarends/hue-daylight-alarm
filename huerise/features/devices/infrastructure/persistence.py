from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from huerise.features.devices.domain import Sound, SoundCategory, SoundRepository
from huerise.infrastructure.database import SoundModel


class SQLSoundRepository(SoundRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def find_by_id(self, sound_id: UUID) -> Sound | None:
        async with self._session_factory() as session:
            orm = await session.get(SoundModel, sound_id)
        return self._to_domain(orm) if orm is not None else None

    async def find_all(self, category: SoundCategory | None = None) -> list[Sound]:
        statement = select(SoundModel)
        if category is not None:
            statement = statement.where(SoundModel.category == category.value)
        statement = statement.order_by(SoundModel.category, SoundModel.name)

        async with self._session_factory() as session:
            result = await session.scalars(statement)
            sounds = result.all()
        return [self._to_domain(sound) for sound in sounds]

    async def save(self, sound: Sound) -> Sound:
        async with self._session_factory.begin() as session:
            orm = await session.merge(
                SoundModel(
                    id=sound.id,
                    name=sound.name,
                    category=sound.category.value,
                    storage_path=sound.storage_path,
                    created_at=sound.created_at,
                )
            )
            await session.flush()
            await session.refresh(orm)
        return self._to_domain(orm)

    @staticmethod
    def _to_domain(orm: SoundModel) -> Sound:
        return Sound(
            id=orm.id,
            name=orm.name,
            category=SoundCategory(orm.category),
            storage_path=orm.storage_path,
            created_at=orm.created_at,
        )
