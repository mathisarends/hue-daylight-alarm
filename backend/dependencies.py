from collections.abc import Generator
from pathlib import Path
from typing import Annotated
from sqlmodel import Session
from fastapi import Depends

from backend.src.infrastructure.audio import AudioRegistry
from backend.src.infrastructure.persistence.database import db_config
from backend.src.infrastructure.persistence.repository import SQLiteAlarmRepository


def get_database_session() -> Generator[Session, None, None]:
    yield from db_config.get_session()


def get_alarm_repository(
    session: Session = Depends(get_database_session),
) -> SQLiteAlarmRepository:
    return SQLiteAlarmRepository(session)


InjectedAlarmRepository = Annotated[
    SQLiteAlarmRepository, Depends(get_alarm_repository)
]


_audio_registry: AudioRegistry | None = None


def get_audio_registry() -> AudioRegistry:
    global _audio_registry

    if _audio_registry is None:
        sounds_dir = Path(__file__).parent.parent / "assets"
        _audio_registry = AudioRegistry(sounds_dir)

    return _audio_registry


InjectedAudioRegistry = Annotated[AudioRegistry, Depends(get_audio_registry)]
