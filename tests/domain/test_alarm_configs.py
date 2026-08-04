from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from huerise.features.alarm.domain import RingtoneConfig, SunriseConfig

SCENE_ID = UUID("22222222-2222-4222-8222-222222222222")


class TestSunriseConfigValidation:
    @pytest.mark.parametrize(
        ("brightness_start", "brightness_end"),
        [(1, 1), (50, 20), (0, 100), (1, 101)],
    )
    def test_rejects_a_non_increasing_or_out_of_bounds_range(
        self, brightness_start: int, brightness_end: int
    ) -> None:
        with pytest.raises(ValueError, match="Invalid brightness range"):
            SunriseConfig(
                scene_id=SCENE_ID,
                scene_name="Sunrise",
                brightness_start=brightness_start,
                brightness_end=brightness_end,
            )

    def test_rejects_a_negative_duration(self) -> None:
        with pytest.raises(ValueError, match="duration must not be negative"):
            SunriseConfig(
                scene_id=SCENE_ID,
                scene_name="Sunrise",
                duration=timedelta(minutes=-1),
            )


class TestRingtoneConfigValidation:
    @pytest.mark.parametrize("volume", [-1, 101])
    def test_rejects_volume_out_of_range(self, volume: int) -> None:
        with pytest.raises(ValueError, match="volume must be 0-100"):
            RingtoneConfig(sound_id=uuid4(), volume=volume)
