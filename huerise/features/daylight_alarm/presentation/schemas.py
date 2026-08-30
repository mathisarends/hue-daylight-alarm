from typing import Literal

from pydantic import BaseModel, Field


class StartRequest(BaseModel):
    duration_seconds: int = Field(gt=0)


class AlarmStatusResponse(BaseModel):
    status: Literal["started"] = "started"
    duration_seconds: int
