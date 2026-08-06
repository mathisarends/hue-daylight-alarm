from typing import Self

from pydantic import BaseModel

from huerise.features.devices.application import DoctorStatus


class DoctorCheckRead(BaseModel):
    configured: bool


class DoctorRead(BaseModel):
    configured: bool
    sonos_speaker: DoctorCheckRead
    hue_bridge: DoctorCheckRead

    @classmethod
    def from_domain(cls, status: DoctorStatus) -> Self:
        return cls(
            configured=status.configured,
            sonos_speaker=DoctorCheckRead(
                configured=status.sonos_speaker.configured
            ),
            hue_bridge=DoctorCheckRead(configured=status.hue_bridge.configured),
        )
