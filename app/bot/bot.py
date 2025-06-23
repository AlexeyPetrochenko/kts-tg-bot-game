import asyncio
import json
import logging

from aio_pika.abc import AbstractIncomingMessage

from app.poller.schemes import Update
from app.store.store import Store
from app.web.config import Config

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, store: Store, queue_id: int) -> None:
        self.store = store
        self.queue_id = queue_id

    async def run_bot(self) -> None:
        self.store.bot_metrics.start_metrics_server()
        await self.store.broker.connect()
        await self.store.tg_api.connect()
        await self.store.database.connect()
        await self.store.game_accessor.connect()
        await self.consume_updates()
        logger.info("Bot queue_id=%s started successfully", self.queue_id)

    async def stop_bot(self) -> None:
        await self.store.database.disconnect()
        await self.store.broker.disconnect()
        await self.store.tg_api.disconnect()
        self.store.bot_metrics.stop_metrics_server()
        logger.info("Bot queue_id=%s stopped successfully", self.queue_id)

    async def consume_updates(self) -> None:
        channel = self.store.broker.channel
        queue = await channel.declare_queue(
            f"update_queue_{self.queue_id}", durable=True
        )
        await queue.consume(callback=self.process_handle_updates)
        await asyncio.Future()

    async def process_handle_updates(
        self, message: AbstractIncomingMessage
    ) -> None:
        body = Update(**json.loads(message.body.decode()))
        await self.store.bot_manager.handle_updates(body)
        await message.ack()


def setup_bot(config: Config, queue_id: int) -> Bot:
    store = Store(config)
    return Bot(store, queue_id)
