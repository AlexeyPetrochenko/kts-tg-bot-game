import asyncio
import json
import logging

from aio_pika.abc import AbstractIncomingMessage

from app.poller.schemes import Update
from app.store.store import Store
from app.web.config import Config

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, store: Store) -> None:
        self.store = store

    async def run_bot(self) -> None:
        await self.store.broker.connect()
        await self.store.tg_api.connect()
        await self.store.database.connect()
        await self.store.game_accessor.connect()
        await self.consume_updates()
        logger.info('Bot started successfully')

    async def stop_bot(self) -> None:
        await self.store.database.disconnect()
        await self.store.broker.disconnect()
        await self.store.tg_api.disconnect()
        logger.info('Bot stopped successfully')

    async def consume_updates(self) -> None:
        channel = self.store.broker.channel
        queue = await channel.declare_queue("updates_queue", durable=True)
        await queue.consume(callback=self.process_handle_updates)
        await asyncio.Future()

    async def process_handle_updates(
        self, message: AbstractIncomingMessage
    ) -> None:
        body = Update(**json.loads(message.body.decode()))
        await self.store.bot_manager.handle_updates(body)
        await message.ack()


def setup_bot(config: Config) -> Bot:
    store = Store(config)
    return Bot(store)
