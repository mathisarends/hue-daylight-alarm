from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Room:
    """A Hue room together with the scenes that can be activated in it."""

    name: str
    scene_names: tuple[str, ...]
