from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class StartRequest(BaseModel):
    # ge, not gt: gt emits OpenAPI 3.1's numeric `exclusiveMinimum`, which the
    # Go CLI's ogen generator cannot parse.
    duration_seconds: int = Field(ge=1)


class AlarmStatusResponse(BaseModel):
    status: Literal["started"] = "started"
    duration_seconds: int


class NamedResourceResponse(BaseModel):
    id: UUID
    name: str


class AfterAlarmConfigurationResponse(BaseModel):
    room: NamedResourceResponse
    scene: NamedResourceResponse
    brightness: int
    delay_seconds: int


class DaylightAlarmConfigurationResponse(BaseModel):
    room: NamedResourceResponse
    scene: NamedResourceResponse
    start_brightness: int
    end_brightness: int
    duration_seconds: int
    after_alarm: AfterAlarmConfigurationResponse | None = None


class AfterAlarmConfigurationRequest(BaseModel):
    room_id: UUID
    scene_id: UUID
    brightness: int = Field(ge=1, le=100)
    delay_seconds: int = Field(ge=0)


class DaylightAlarmConfigurationRequest(BaseModel):
    room_id: UUID
    scene_id: UUID
    start_brightness: int = Field(ge=1, le=100)
    end_brightness: int = Field(ge=1, le=100)
    duration_seconds: int = Field(ge=1)
    after_alarm: AfterAlarmConfigurationRequest | None = None

    @model_validator(mode="after")
    def require_increasing_brightness(self) -> DaylightAlarmConfigurationRequest:
        if self.end_brightness <= self.start_brightness:
            raise ValueError("end_brightness must be greater than start_brightness")
        return self
