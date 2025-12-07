from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from daylight_alarm.domain.value_objects import AlarmStatus, EasingType


class AlarmModel(SQLModel, table=True):
    __tablename__ = "alarms"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    name: str = Field(max_length=100)
    room_name: str = Field(max_length=100)
    scene_name: str = Field(max_length=100)

    duration_minutes: int = Field(ge=1, le=60)
    brightness_start: int = Field(ge=0, le=100)
    brightness_end: int = Field(ge=0, le=100)
    steps_count: int = Field(ge=1)

    sound_profile_name: str | None = Field(default=None, max_length=50)

    easing_type: EasingType = Field(default=EasingType.LINEAR)

    status: AlarmStatus = Field(default=AlarmStatus.PENDING)
    current_step: int = Field(default=0)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
