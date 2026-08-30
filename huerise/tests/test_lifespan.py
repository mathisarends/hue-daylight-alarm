from types import SimpleNamespace
from unittest.mock import AsyncMock

from huerise.lifecycle import Runnable
from huerise.lifespan import lifespan


async def test_runnables_start_in_order_and_stop_in_reverse() -> None:
    calls: list[str] = []

    def runnable(name: str) -> Runnable:
        item = AsyncMock(spec=Runnable)
        item.start.side_effect = lambda: calls.append(f"start {name}")
        item.stop.side_effect = lambda: calls.append(f"stop {name}")
        return item

    first = runnable("first")
    second = runnable("second")
    container = AsyncMock()
    container.get.return_value = [first, second]
    container.close.side_effect = lambda: calls.append("close")
    app = SimpleNamespace(state=SimpleNamespace(dishka_container=container))

    async with lifespan(app):
        calls.append("running")

    assert calls == [
        "start first",
        "start second",
        "running",
        "stop second",
        "stop first",
        "close",
    ]
    container.get.assert_awaited_once_with(list[Runnable])
