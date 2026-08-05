from unittest.mock import MagicMock

from huerise.features.devices.application import LightChangeLogger, LightEvents


async def test_logger_subscription_is_owned_by_its_lifecycle() -> None:
    events = MagicMock(spec=LightEvents)

    logger = LightChangeLogger(events)

    events.subscribe.assert_not_called()

    await logger.start()
    events.subscribe.assert_called_once_with(logger._log)

    await logger.stop()
    events.unsubscribe.assert_called_once_with(logger._log)
