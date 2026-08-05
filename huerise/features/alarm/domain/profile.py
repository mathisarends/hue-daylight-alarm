from dataclasses import replace
from uuid import UUID

from huerise.features.alarm.domain.views import (
    IntroConfig,
    RingtoneConfig,
    SunriseConfig,
)
from huerise.shared.ddd import Aggregate


class AlarmProfile(Aggregate):
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
        super().__init__(id)
        self.name = name
        self.intro_config = intro_config
        self.sunrise_config = sunrise_config
        self.ringtone_config = ringtone_config
        self.is_default = is_default

    def use_scene(self, scene_id: UUID, scene_name: str) -> bool:
        """Point the sunrise at a Hue scene, keeping the rest of the curve.

        Reports whether that moved, so the caller can decide to notify.
        """
        sunrise = self.sunrise_config
        if sunrise.scene_id == scene_id and sunrise.scene_name == scene_name:
            return False
        self.sunrise_config = replace(sunrise, scene_id=scene_id, scene_name=scene_name)
        return True
