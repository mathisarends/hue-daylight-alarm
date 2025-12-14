from abc import ABC, abstractmethod
import asyncio
from typing import Protocol
from uuid import UUID

from backend.src.domain.aggregates import SunriseAlarm
from backend.src.domain.events import (
    AlarmCancelled,
    AlarmCompleted,
    AlarmStarted,
    BrightnessChangeRequested,
    DomainEvent,
    WaitRequested,
)
from backend.src.domain.value_objects import Brightness
from backend.src.infrastructure.ports import AudioService


class RoomService(Protocol):
    async def activate_scene(self, room_name: str, scene_name: str) -> None: ...
    async def set_brightness(self, room_name: str, brightness: Brightness) -> None: ...


class EventHandler(ABC):
    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        pass

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        pass


class AlarmStartedHandler(EventHandler):
    def __init__(self, room_service: RoomService):
        self._room_service = room_service

    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, AlarmStarted)

    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, AlarmStarted):
            return

        await self._room_service.activate_scene(event.room_name, event.scene_name)


class BrightnessChangeRequestedHandler(EventHandler):
    def __init__(self, room_service: RoomService):
        self._room_service = room_service

    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, BrightnessChangeRequested)

    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, BrightnessChangeRequested):
            return

        await self._room_service.set_brightness(event.room_name, event.brightness)


class WaitRequestedHandler(EventHandler):
    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, WaitRequested)

    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, WaitRequested):
            return

        await asyncio.sleep(event.duration_seconds)


class AlarmAudioHandler(Protocol):
    def register_alarm(self, alarm: SunriseAlarm) -> None: ...


class AudioOnAlarmStartedHandler(EventHandler, AlarmAudioHandler):
    def __init__(self, audio_service: AudioService):
        self._audio_service = audio_service
        self._alarms: dict[UUID, SunriseAlarm] = {}

    def register_alarm(self, alarm: SunriseAlarm) -> None:
        self._alarms[alarm.id] = alarm

    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, AlarmStarted)

    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, AlarmStarted):
            return

        alarm = self._alarms.get(event.aggregate_id)
        if alarm and alarm.sound_profile:
            audio_file = alarm.sound_profile.wake_up_sound
            await self._audio_service.play(audio_file)


class AudioOnAlarmCompletedHandler(EventHandler, AlarmAudioHandler):
    def __init__(self, audio_service: AudioService):
        self._audio_service = audio_service
        self._alarms: dict[UUID, SunriseAlarm] = {}

    def register_alarm(self, alarm: SunriseAlarm) -> None:
        self._alarms[alarm.id] = alarm

    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, AlarmCompleted)

    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, AlarmCompleted):
            return

        alarm = self._alarms.get(event.aggregate_id)
        if alarm and alarm.sound_profile:
            audio_file = alarm.sound_profile.get_up_sound
            await self._audio_service.play(audio_file)


class AudioOnAlarmCancelledHandler(EventHandler):
    def __init__(self, audio_service: AudioService):
        self._audio_service = audio_service

    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, AlarmCancelled)

    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, AlarmCancelled):
            return

        await self._audio_service.stop()
