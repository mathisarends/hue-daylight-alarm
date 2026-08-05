from typing import Protocol


class Runnable(Protocol):
    async def start(self) -> None: ...

    async def stop(self) -> None: ...
