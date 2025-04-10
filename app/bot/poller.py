import asyncio
import logging
import typing
from asyncio import Future, Task

if typing.TYPE_CHECKING:
    from app.store import Store

logger = logging.getLogger(__name__)


class Poller:
    def __init__(self, store: "Store") -> None:
        self.store = store
        self.is_running = False
        self.poll_task: Task | None = None

    def start(self) -> None:
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())
        self.poll_task.add_done_callback(self._done_callback)

    async def stop(self) -> None:
        self.is_running = False
        if self.poll_task:
            await self.poll_task

    def _done_callback(self, result: Future) -> None:
        if result.exception():
            logger.error(
                "poller stopped with exception", exc_info=result.exception()
            )
        if self.is_running and not self.store.tg_api.session.closed:
            self.start()
            logger.info("Restart Poller")

    async def poll(self) -> None:
        while self.is_running:
            await self.store.tg_api.poll()
