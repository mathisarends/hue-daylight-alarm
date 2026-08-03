import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class AlarmModel(SQLModel, table=True):
    __tablename__ = "alarms"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    label: str
    status: str
    alarm_type: str
    series_id: uuid.UUID | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Schedule (flattened)
    schedule_hour: int
    schedule_minute: int
    schedule_recurrence: str | None = Field(default=None)  # JSON: [0, 1, 4]

    # IntroConfig
    intro_audio_file: str

    # SunriseConfig
    sunrise_room_name: str
    sunrise_scene_name: str = "Tageslichtwecker"
    sunrise_duration_minutes: int = 7
    sunrise_brightness_start: int = 1
    sunrise_brightness_end: int = 100
    sunrise_steps: int = 70

    # RingtoneConfig
    ringtone_audio_file: str
    ringtone_volume: int = 80
