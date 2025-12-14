from collections.abc import Generator
from typing import Annotated
from sqlmodel import Session
from fastapi import Depends

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
