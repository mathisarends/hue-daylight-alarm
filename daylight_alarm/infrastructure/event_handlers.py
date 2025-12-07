from abc import ABC, abstractmethod
import asyncio
from typing import Protocol

from daylight_alarm.domain.events import AlarmCompleted, AlarmStarted, BrightnessChangeRequested, DomainEvent, WaitRequested
from daylight_alarm.domain.value_objects import AlarmSounds, Brightness
from daylight_alarm.infrastructure.ports import AudioService


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


class AudioOnAlarmStartedHandler(EventHandler):
    def __init__(self, audio_service: AudioService, alarm_sounds: AlarmSounds):
        self._audio_service = audio_service
        self._alarm_sounds = alarm_sounds
    
    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, AlarmStarted)
    
    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, AlarmStarted):
            return
        
        if self._alarm_sounds.startup_sound:
            await self._audio_service.play(self._alarm_sounds.startup_sound)


class AudioOnAlarmCompletedHandler(EventHandler):
    def __init__(self, audio_service: AudioService, alarm_sounds: AlarmSounds):
        self._audio_service = audio_service
        self._alarm_sounds = alarm_sounds
    
    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, AlarmCompleted)
    
    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, AlarmCompleted):
            return
        
        await self._audio_service.play(self._alarm_sounds.completion_sound)