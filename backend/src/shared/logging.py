import logging
import os
from typing import ClassVar

from dotenv import load_dotenv

load_dotenv(override=True)

_APP_NAME = "daylight_alarm"

logger = logging.getLogger(_APP_NAME)
logger.addHandler(logging.NullHandler())


def _configure_library_logging(level: str = "WARNING") -> None:
    log_level = getattr(logging, level.upper(), logging.WARNING)
    logging.getLogger(_APP_NAME).setLevel(log_level)


def _auto_configure_from_environment() -> None:
    env_log_level = os.getenv(f"{_APP_NAME.upper()}_LOG_LEVEL")
    if env_log_level:
        _configure_library_logging(env_log_level)


_auto_configure_from_environment()


class LoggingMixin:
    logger: ClassVar[logging.Logger] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.logger = logging.getLogger(f"{_APP_NAME}.{cls.__name__}")

    @property
    def instance_logger(self) -> logging.Logger:
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(f"{_APP_NAME}.{self.__class__.__name__}")
        return self._logger
