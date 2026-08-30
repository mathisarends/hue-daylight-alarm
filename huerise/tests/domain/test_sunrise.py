from datetime import timedelta

import pytest

from huerise.features.lighting.domain import SunriseRamp, sunrise_steps

STEP = timedelta(seconds=6)


class TestSunriseRamp:
    def test_rejects_a_range_that_does_not_climb(self) -> None:
        with pytest.raises(ValueError, match="brightness range"):
            SunriseRamp(
                duration=timedelta(minutes=1), brightness_start=80, brightness_end=80
            )

    def test_rejects_a_negative_duration(self) -> None:
        with pytest.raises(ValueError, match="duration"):
            SunriseRamp(duration=timedelta(seconds=-1))


class TestSunriseSteps:
    def test_derives_step_count_from_duration(self) -> None:
        ramp = SunriseRamp(duration=timedelta(minutes=1))

        assert len(list(sunrise_steps(ramp, STEP))) == 10

    def test_walks_from_start_to_end_brightness(self) -> None:
        ramp = SunriseRamp(
            duration=timedelta(minutes=1), brightness_start=10, brightness_end=100
        )

        brightness = [step.brightness for step in sunrise_steps(ramp, STEP)]

        assert brightness[0] == 10
        assert brightness[-1] == 100
        assert brightness == sorted(brightness)

    def test_always_yields_at_least_one_step(self) -> None:
        ramp = SunriseRamp(duration=timedelta(0))

        assert [step.brightness for step in sunrise_steps(ramp, STEP)] == [1]

    def test_each_step_knows_its_place_in_the_whole_sunrise(self) -> None:
        ramp = SunriseRamp(duration=timedelta(minutes=1))

        steps = list(sunrise_steps(ramp, STEP))

        assert [step.index for step in steps] == list(range(10))
        assert {step.total for step in steps} == {10}
        assert steps[3].elapsed_seconds == 18
        assert steps[3].total_seconds == 60

    def test_a_shorter_interval_packs_the_same_climb_into_more_steps(self) -> None:
        """What a demo relies on: same curve, same ends, finer granularity."""
        ramp = SunriseRamp(duration=timedelta(seconds=20))

        steps = list(sunrise_steps(ramp, timedelta(seconds=1)))

        assert len(steps) == 20
        assert steps[0].brightness == 1
        assert steps[-1].brightness == 100
