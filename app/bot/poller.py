import asyncio
import logging
import typing
from asyncio import Task

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
        logger.info("Polling started")

    async def stop(self) -> None:
        self.is_running = False
        if self.poll_task:
            await self.poll_task
        logger.info("Poller Stopped")

    async def poll(self) -> None:
        while self.is_running:
            try:
                await self.store.tg_api.poll()
            except Exception as e:
                logger.error("poller stopped with exception: %s", e)
                await asyncio.sleep(5)
