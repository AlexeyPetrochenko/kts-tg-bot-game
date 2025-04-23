import asyncio
import hashlib
import logging
from asyncio import Task
from typing import Any

import aio_pika
from pydantic import ValidationError

from app.poller.schemes import CallbackQuery, Message, Update
from app.store import Store
from app.web.config import Config

logger = logging.getLogger(__name__)


class Poller:
    def __init__(self, store: "Store") -> None:
        self.store = store
        self.is_running = False
        self.poll_task: Task | None = None
        self.offset: int | None = None
        self.timeout: int = 30

    async def start(self) -> None:
        self.is_running = True
        await self.store.tg_api.connect()
        await self.store.broker.connect()
        await self._initialize_queues()
        self.poll_task = asyncio.create_task(self.poll())
        logger.info("Polling started")

    async def stop(self) -> None:
        self.is_running = False
        if self.poll_task:
            await self.poll_task
        await self.store.broker.disconnect()
        await self.store.tg_api.disconnect()
        logger.info("Poller Stopped")

    async def _initialize_queues(self) -> None:
        channel = self.store.broker.channel
        for i in range(self.store.config.broker.number_queues):
            queue_name = f"update_queue_{i}"
            await channel.declare_queue(queue_name, durable=True)
            logger.info("Queue %s declared", queue_name)

    async def poll(self) -> None:
        while self.is_running:
            try:
                updates = await self.store.tg_api.fetch_updates(
                    self.offset, self.timeout
                )
                for update in updates["result"]:
                    update_scheme = self._parse_update(update)
                    if isinstance(update_scheme, Update):
                        message = self.create_amqp_message(update_scheme)
                        try:
                            await self.add_to_queue(message)
                        except aio_pika.exceptions.AMQPException as e:
                            logger.error("Failed send message to queue: %s", e)
                        self.offset = update_scheme.update_id + 1
                    else:
                        self.offset = update_scheme + 1
            except Exception as e:
                logger.error("poller stopped with exception: %s", e)
                await asyncio.sleep(5)

    def create_amqp_message(self, data: Update) -> aio_pika.Message:
        return aio_pika.Message(
            body=data.model_dump_json().encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            headers={
                "message_type": "telegram_update",
                "encoding": "utf-8",
                "chat_id": str(data.body.chat_id),
            },
        )

    async def add_to_queue(self, message: aio_pika.Message) -> None:
        chat_id = message.headers.get("chat_id")
        queue_name = self.calculate_queue_name(
            chat_id, self.store.config.broker.number_queues
        )
        channel = self.store.broker.channel
        await channel.default_exchange.publish(message, routing_key=queue_name)

    @staticmethod
    def calculate_queue_name(chat_id: Any, num_queues: int) -> str:
        hashed_chat_id = hashlib.sha256(str(chat_id).encode()).hexdigest()
        queue_id = int(hashed_chat_id, 16) % num_queues
        return f"update_queue_{queue_id}"

    def _parse_update(self, update: dict) -> Update | int:
        try:
            if "callback_query" in update:
                return Update(
                    update_id=update["update_id"],
                    date=update["callback_query"]["message"]["date"],
                    body=CallbackQuery(
                        callback_id=update["callback_query"]["id"],
                        chat_id=update["callback_query"]["message"]["chat"][
                            "id"
                        ],
                        command=update["callback_query"]["data"],
                        message_id=update["callback_query"]["message"][
                            "message_id"
                        ],
                        from_id=update["callback_query"]["from"]["id"],
                        from_username=update["callback_query"]["from"][
                            "first_name"
                        ],
                    ),
                )

            return Update(
                update_id=update["update_id"],
                date=update["message"]["date"],
                body=Message(
                    chat_id=update["message"]["chat"]["id"],
                    text=update["message"].get("text", ""),
                    message_id=update["message"]["message_id"],
                    from_id=update["message"]["from"]["id"],
                    from_username=update["message"]["from"]["first_name"],
                ),
            )

        except (KeyError, TypeError, ValidationError) as e:
            logger.error(
                "An update with an incorrect structure was missed. [%s]", e
            )
            return update.get("update_id", -1)


def setup_poller(config: Config) -> Poller:
    store = Store(config)
    return Poller(store)
