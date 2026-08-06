from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from huerise.features.devices.domain import (
    SonosSpeaker,
    SonosSpeakerRepository,
    Sound,
    SoundCategory,
    SoundRepository,
)
from huerise.infrastructure.database import SonosSpeakerSelectionModel, SoundModel

_SONOS_SELECTION_ID = UUID("0198f9b4-0000-7000-8000-000000000001")


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


class SQLSonosSpeakerRepository(SonosSpeakerRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_selected(self) -> SonosSpeaker | None:
        async with self._session_factory() as session:
            orm = await session.get(SonosSpeakerSelectionModel, _SONOS_SELECTION_ID)
        if orm is None:
            return None
        return self._to_domain(orm)

    async def save_selected(self, speaker: SonosSpeaker) -> SonosSpeaker:
        async with self._session_factory.begin() as session:
            orm = await session.merge(
                SonosSpeakerSelectionModel(
                    id=_SONOS_SELECTION_ID,
                    speaker_id=speaker.id,
                    speaker_name=speaker.name,
                    ip_address=speaker.ip_address,
                    group_id=speaker.group_id,
                    is_coordinator=speaker.is_coordinator,
                )
            )
            await session.flush()
            await session.refresh(orm)
        return self._to_domain(orm)

    @staticmethod
    def _to_domain(orm: SonosSpeakerSelectionModel) -> SonosSpeaker:
        return SonosSpeaker(
            id=orm.speaker_id,
            name=orm.speaker_name,
            ip_address=orm.ip_address,
            group_id=orm.group_id,
            is_coordinator=orm.is_coordinator,
        )
