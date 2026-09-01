from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


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
    delay_seconds: int


class DaylightAlarmConfigurationResponse(BaseModel):
    room: NamedResourceResponse
    scene: NamedResourceResponse
    duration_seconds: int
    after_alarm: AfterAlarmConfigurationResponse | None = None


class AfterAlarmConfigurationRequest(BaseModel):
    room_id: UUID
    scene_id: UUID
    delay_seconds: int = Field(ge=0)


class DaylightAlarmConfigurationRequest(BaseModel):
    room_id: UUID
    scene_id: UUID
    duration_seconds: int = Field(ge=1)
    after_alarm: AfterAlarmConfigurationRequest | None = None
