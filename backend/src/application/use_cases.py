from typing import Callable

from backend.src.application.alarm_scheduler import AlarmScheduler
from backend.src.application.event_dispatcher import EventDispatcher
from backend.src.domain.aggregates import SunriseAlarm
from backend.src.domain.easing import ease_in_cubic
from backend.src.domain.value_objects import (
    BrightnessRange,
    Duration,
    ScheduledTime,
    SoundProfile,
    TransitionSteps,
)
from backend.src.infrastructure.event_handlers import AlarmAudioHandler


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


class ScheduleAlarmUseCase:
    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        alarm_scheduler: AlarmScheduler,
        audio_handlers: list[AlarmAudioHandler] = None,
    ):
        self.event_dispatcher = event_dispatcher
        self.alarm_scheduler = alarm_scheduler
        self.audio_handlers = audio_handlers if audio_handlers is not None else []

    async def execute(
        self,
        room_name: str,
        hour: int,
        minute: int,
        duration_minutes: int = 7,
        easing: Callable[[float], float] = ease_in_cubic,
        sound_profile: SoundProfile | None = None,
    ) -> SunriseAlarm:
        scheduled_time = ScheduledTime(hour=hour, minute=minute)

        alarm = SunriseAlarm(
            room_name=room_name,
            duration=Duration(minutes=duration_minutes),
            brightness_range=BrightnessRange(start=1, end=100),
            steps=TransitionSteps(count=70),
            easing_function=easing,
            sound_profile=sound_profile,
            scheduled_time=scheduled_time,
        )

        for handler in self.audio_handlers:
            handler.register_alarm(alarm)

        alarm.schedule()

        self.alarm_scheduler.register_alarm(alarm)

        await self.event_dispatcher.dispatch_all(alarm.collect_events())

        return alarm


class TriggerScheduledAlarmUseCase:
    def __init__(
        self,
        event_dispatcher: EventDispatcher,
    ):
        self.event_dispatcher = event_dispatcher

    async def execute(self, alarm: SunriseAlarm) -> SunriseAlarm:
        if alarm.scheduled_time is None:
            raise ValueError("Alarm is not scheduled")

        alarm.trigger()
        await self.event_dispatcher.dispatch_all(alarm.collect_events())

        while not alarm.is_finished:
            alarm.progress_step()
            await self.event_dispatcher.dispatch_all(alarm.collect_events())

        return alarm
