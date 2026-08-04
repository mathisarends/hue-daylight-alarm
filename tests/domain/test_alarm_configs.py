from datetime import timedelta
from uuid import uuid4

import pytest

from huerise.features.alarm.domain import RingtoneConfig, SunriseConfig


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
                brightness_start=brightness_start, brightness_end=brightness_end
            )

    def test_rejects_a_negative_duration(self) -> None:
        with pytest.raises(ValueError, match="duration must not be negative"):
            SunriseConfig(duration=timedelta(minutes=-1))


class TestRingtoneConfigValidation:
    @pytest.mark.parametrize("volume", [-1, 101])
    def test_rejects_volume_out_of_range(self, volume: int) -> None:
        with pytest.raises(ValueError, match="volume must be 0-100"):
            RingtoneConfig(sound_id=uuid4(), volume=volume)
