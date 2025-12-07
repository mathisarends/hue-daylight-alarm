import asyncio
from pathlib import Path

from daylight_alarm.application.event_dispatcher import EventDispatcher
from daylight_alarm.application.use_cases import StartSunriseAlarmUseCase
from daylight_alarm.domain.easing import ease_in_cubic
from daylight_alarm.infrastructure.adapters import HueifyRoomService
from daylight_alarm.infrastructure.adapters.audio_apapter import PygameAudioService
from daylight_alarm.infrastructure.event_handlers import (
    AlarmStartedHandler,
    AudioOnAlarmStartedHandler,
    AudioOnAlarmCompletedHandler,
    BrightnessChangeRequestedHandler,
    WaitRequestedHandler,
)
from daylight_alarm.infrastructure.sound_profiles import SoundProfileRepository


def select_sound_profile(sound_repo: SoundProfileRepository):
    profiles = sound_repo.list_all()

    print("\n" + "=" * 60)
    print("Available sound profiles:")
    print("=" * 60)
    for i, profile in enumerate(profiles, 1):
        print(f"\n{i}. {profile.name}")
        print(f"   {profile.description}")
        print(f"   Wake-up: {profile.wake_up_sound.path.stem}")
        print(f"   Get-up: {profile.get_up_sound.path.stem}")
    print("=" * 60 + "\n")

    while True:
        try:
            choice = input(f"Select profile (1-{len(profiles)}): ")
            choice_num = int(choice)
            if 1 <= choice_num <= len(profiles):
                return profiles[choice_num - 1]
        except (ValueError, KeyboardInterrupt):
            print("\nExiting...")
            exit(0)
        print("Invalid choice, please try again.")


async def main():
    # Sound-Profile laden
    sound_repo = SoundProfileRepository(assets_path=Path("assets"))

    # Interaktive Auswahl oder Default
    try:
        selected_profile = select_sound_profile(sound_repo)
    except KeyboardInterrupt:
        print("\nExiting...")
        return

    print(f"\n✓ Selected profile: {selected_profile.name}")
    print(f"  Wake-up: {selected_profile.wake_up_sound.path.name}")
    print(f"  Get-up: {selected_profile.get_up_sound.path.name}\n")

    # Services
    room_service = HueifyRoomService()
    audio_service = PygameAudioService()

    # Audio Handler
    audio_started_handler = AudioOnAlarmStartedHandler(audio_service)
    audio_completed_handler = AudioOnAlarmCompletedHandler(audio_service)

    # Alle Handler registrieren
    handlers = [
        AlarmStartedHandler(room_service),
        BrightnessChangeRequestedHandler(room_service),
        WaitRequestedHandler(),
        audio_started_handler,
        audio_completed_handler,
    ]

    dispatcher = EventDispatcher(handlers)
    use_case = StartSunriseAlarmUseCase(
        dispatcher, audio_handlers=[audio_started_handler, audio_completed_handler]
    )

    alarm = await use_case.execute(
        room_name="Zimmer 1",
        duration_minutes=1,
        easing=ease_in_cubic,
        sound_profile=selected_profile,
    )

    print(f"\nAlarm {alarm.id} finished with status: {alarm.status}")


if __name__ == "__main__":
    asyncio.run(main())
