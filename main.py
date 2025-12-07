import asyncio
from hueify import Room

from daylight_alarm.application.event_dispatcher import EventDispatcher
from daylight_alarm.application.use_cases import StartSunriseAlarmUseCase
from daylight_alarm.domain.easing import ease_in_cubic
from daylight_alarm.infrastructure.adapters import HueifyRoomService
from daylight_alarm.infrastructure.event_handlers import AlarmStartedHandler, BrightnessChangeRequestedHandler, WaitRequestedHandler

async def main():
    room_service = HueifyRoomService()
    
    handlers = [
        AlarmStartedHandler(room_service),
        BrightnessChangeRequestedHandler(room_service),
        WaitRequestedHandler()
    ]
    
    dispatcher = EventDispatcher(handlers)
    
    use_case = StartSunriseAlarmUseCase(dispatcher)
    
    alarm = await use_case.execute(
        room_name="Zimmer 1",
        duration_minutes=1,
        easing=ease_in_cubic
    )
    
    print(f"Alarm {alarm.id} finished with status: {alarm.status}")


if __name__ == "__main__":
    asyncio.run(main())