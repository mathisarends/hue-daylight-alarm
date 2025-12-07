from typing import Callable

from daylight_alarm.application.event_dispatcher import EventDispatcher
from daylight_alarm.domain.aggregates import SunriseAlarm
from daylight_alarm.domain.easing import ease_in_cubic
from daylight_alarm.domain.value_objects import (
    BrightnessRange,
    Duration,
    SoundProfile,
    TransitionSteps,
)
from daylight_alarm.infrastructure.event_handlers import AlarmAudioHandler


class StartSunriseAlarmUseCase:
    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        audio_handlers: list[AlarmAudioHandler] = None,
    ):
        self.event_dispatcher = event_dispatcher
        self.audio_handlers = audio_handlers if audio_handlers is not None else []

    async def execute(
        self,
        room_name: str,
        duration_minutes: int = 1,
        easing: Callable[[float], float] = ease_in_cubic,
        sound_profile: SoundProfile | None = None,
    ) -> SunriseAlarm:
        alarm = SunriseAlarm(
            room_name=room_name,
            duration=Duration(minutes=duration_minutes),
            brightness_range=BrightnessRange(start=1, end=100),
            steps=TransitionSteps(count=70),
            easing_function=easing,
            sound_profile=sound_profile,
        )

        for handler in self.audio_handlers:
            handler.register_alarm(alarm)

        alarm.start()
        await self.event_dispatcher.dispatch_all(alarm.collect_events())

        while not alarm.is_finished:
            alarm.progress_step()
            await self.event_dispatcher.dispatch_all(alarm.collect_events())

        return alarm
