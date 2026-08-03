from uuid import UUID, uuid4

from huerise.features.alarm.domain.views import (
    IntroConfig,
    RingtoneConfig,
    SunriseConfig,
)


class AlarmProfile:
    """Reusable behaviour of an alarm: intro, sunrise curve, ringtone."""

    def __init__(
        self,
        name: str,
        intro_config: IntroConfig,
        sunrise_config: SunriseConfig,
        ringtone_config: RingtoneConfig,
        is_default: bool = False,
        id: UUID | None = None,
    ) -> None:
        self.id = id if id is not None else uuid4()
        self.name = name
        self.intro_config = intro_config
        self.sunrise_config = sunrise_config
        self.ringtone_config = ringtone_config
        self.is_default = is_default
