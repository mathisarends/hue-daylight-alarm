from typing import Self

from pydantic import BaseModel

from huerise.features.devices.application import DoctorStatus


class DoctorCheckRead(BaseModel):
    configured: bool


class DoctorRead(BaseModel):
    configured: bool
    hue_bridge: DoctorCheckRead

    @classmethod
    def from_domain(cls, status: DoctorStatus) -> Self:
        return cls(
            configured=status.configured,
            hue_bridge=DoctorCheckRead(configured=status.hue_bridge.configured),
        )
