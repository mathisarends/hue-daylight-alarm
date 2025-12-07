from uuid import UUID
from sqlmodel import Session, select
from daylight_alarm.domain.aggregates import SunriseAlarm
from daylight_alarm.infrastructure.persistence.models import AlarmModel
from daylight_alarm.infrastructure.persistence.mappers import to_model, to_domain


class SQLiteAlarmRepository:
    def __init__(self, session: Session):
        self._session = session

    def save(self, alarm: SunriseAlarm) -> SunriseAlarm:
        model = to_model(alarm)

        existing = self._session.get(AlarmModel, alarm.id)
        if existing:
            for key, value in model.model_dump(exclude={"created_at"}).items():
                setattr(existing, key, value)
            self._session.add(existing)
        else:
            self._session.add(model)

        self._session.commit()
        self._session.refresh(model if not existing else existing)

        return to_domain(model if not existing else existing)

    def find_by_id(self, alarm_id: UUID) -> SunriseAlarm | None:
        model = self._session.get(AlarmModel, alarm_id)
        if not model:
            return None
        return to_domain(model)

    def find_all(self) -> list[SunriseAlarm]:
        statement = select(AlarmModel)
        models = self._session.exec(statement).all()
        return [to_domain(model) for model in models]

    def delete(self, alarm_id: UUID) -> bool:
        model = self._session.get(AlarmModel, alarm_id)
        if not model:
            return False

        self._session.delete(model)
        self._session.commit()
        return True

    def exists(self, alarm_id: UUID) -> bool:
        return self._session.get(AlarmModel, alarm_id) is not None
