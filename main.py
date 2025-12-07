# main.py
import asyncio
from pathlib import Path

from daylight_alarm.application.event_dispatcher import EventDispatcher
from daylight_alarm.application.use_cases import StartSunriseAlarmUseCase
from daylight_alarm.domain.easing import ease_in_cubic
from daylight_alarm.domain.value_objects import AlarmSounds, AudioFile
from daylight_alarm.infrastructure.adapters import HueifyRoomService, PygameAudioService
from daylight_alarm.infrastructure.event_handlers import (
    AlarmStartedHandler,
    AudioOnAlarmStartedHandler,
    AudioOnAlarmCompletedHandler,
    BrightnessChangeRequestedHandler,
    WaitRequestedHandler,
)


async def main():
    alarm_sounds = AlarmSounds(
        startup_sound=AudioFile(Path("sounds/gentle_chime.mp3")),
        completion_sound=AudioFile(Path("sounds/alarm_bell.mp3"))
    )
    
    room_service = HueifyRoomService()
    audio_service = PygameAudioService()
    
    handlers = [
        AlarmStartedHandler(room_service),
        BrightnessChangeRequestedHandler(room_service),
        WaitRequestedHandler(),
        AudioOnAlarmStartedHandler(audio_service, alarm_sounds),
        AudioOnAlarmCompletedHandler(audio_service, alarm_sounds),
    ]
    
    dispatcher = EventDispatcher(handlers)
    use_case = StartSunriseAlarmUseCase(dispatcher)
    
    alarm = await use_case.execute(
        room_name="Zimmer 1",
        duration_minutes=7,
        easing=ease_in_cubic
    )
    
    print(f"Alarm {alarm.id} finished with status: {alarm.status}")


if __name__ == "__main__":
    asyncio.run(main())