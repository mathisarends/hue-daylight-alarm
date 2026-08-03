from huerise.presentation import Feature

from .infrastructure import RunnerProvider

feature = Feature(name="runner", providers=[RunnerProvider])

__all__ = ["feature"]
