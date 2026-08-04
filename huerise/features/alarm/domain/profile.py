from uuid import UUID

from huerise.features.alarm.domain.views import (
    IntroSettings,
    RingtoneSettings,
    SunriseSettings,
)
from huerise.shared.ddd import Aggregate


class AlarmProfile(Aggregate):
    """Reusable behaviour of an alarm: intro, sunrise curve, ringtone."""

    def __init__(
        self,
        name: str,
        intro_settings: IntroSettings,
        sunrise_settings: SunriseSettings,
        ringtone_settings: RingtoneSettings,
        is_default: bool = False,
        id: UUID | None = None,
    ) -> None:
        super().__init__(id)
        self.name = name
        self.intro_settings = intro_settings
        self.sunrise_settings = sunrise_settings
        self.ringtone_settings = ringtone_settings
        self.is_default = is_default
