import asyncio
from collections.abc import Callable, Coroutine
from typing import Any


class FsmTimerManager:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._timeout_task: asyncio.Task | None = None

    def start(
        self,
        seconds: int,
        on_timeout: Callable[[], Coroutine[Any, Any, None]],
    ) -> None:
        self.cancel()

        async def _run() -> None:
            try:
                await asyncio.sleep(seconds)
            except asyncio.CancelledError:
                return
            self._timeout_task = asyncio.create_task(on_timeout())

        self._task = asyncio.create_task(_run())

    def cancel(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None
