from daylight_alarm.domain.aggregates import SunriseAlarm
from daylight_alarm.domain.easing import ease_in_cubic, ease_in_quad, ease_linear
from daylight_alarm.domain.value_objects import (
    BrightnessRange,
    Duration,
    EasingType,
    TransitionSteps,
)
from daylight_alarm.infrastructure.persistence.models import AlarmModel


_EASING_TO_ENUM = {
    ease_linear: EasingType.LINEAR,
    ease_in_quad: EasingType.EASE_IN_QUAD,
    ease_in_cubic: EasingType.EASE_IN_CUBIC,
}

_ENUM_TO_EASING = {
    EasingType.LINEAR: ease_linear,
    EasingType.EASE_IN_QUAD: ease_in_quad,
    EasingType.EASE_IN_CUBIC: ease_in_cubic,
}


def to_model(alarm: SunriseAlarm, name: str = None) -> AlarmModel:
    easing_enum = _EASING_TO_ENUM.get(alarm._easing_function, EasingType.LINEAR)

    return AlarmModel(
        id=alarm.id,
        name=name or alarm.room_name,
        room_name=alarm.room_name,
        scene_name=alarm.scene_name,
        duration_minutes=alarm._duration.minutes,
        brightness_start=alarm._brightness_range.start,
        brightness_end=alarm._brightness_range.end,
        steps_count=alarm._steps.count,
        sound_profile_name=alarm.sound_profile.name if alarm.sound_profile else None,
        easing_type=easing_enum,
        status=alarm.status,
        current_step=alarm._current_step,
    )


def to_domain(model: AlarmModel, sound_profile=None) -> SunriseAlarm:
    easing_func = _ENUM_TO_EASING.get(model.easing_type, ease_linear)

    alarm = SunriseAlarm(
        room_name=model.room_name,
        scene_name=model.scene_name,
        duration=Duration(minutes=model.duration_minutes),
        brightness_range=BrightnessRange(
            start=model.brightness_start, end=model.brightness_end
        ),
        steps=TransitionSteps(count=model.steps_count),
        easing_function=easing_func,
        sound_profile=sound_profile,
    )

    alarm._id = model.id
    alarm._status = model.status
    alarm._current_step = model.current_step

    return alarm
