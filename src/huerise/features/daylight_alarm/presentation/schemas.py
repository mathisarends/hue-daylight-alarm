from typing import Literal

from pydantic import BaseModel, Field


class StartRequest(BaseModel):
    # ge, not gt: gt emits OpenAPI 3.1's numeric `exclusiveMinimum`, which the
    # Go CLI's ogen generator cannot parse.
    duration_seconds: int = Field(ge=1)


class AlarmStatusResponse(BaseModel):
    status: Literal["started"] = "started"
    duration_seconds: int
