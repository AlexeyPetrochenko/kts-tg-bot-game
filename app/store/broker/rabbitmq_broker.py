import logging
import typing

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractRobustConnection

if typing.TYPE_CHECKING:
    from app.store.store import Store


logger = logging.getLogger(__name__)


class RabbitMQClient:
    def __init__(self, store: "Store") -> None:
        self.store = store
        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractChannel | None = None

    async def connect(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        self.connection = await aio_pika.connect_robust(
            self.store.config.broker.RABBIT_MQ_URL
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(
            prefetch_count=self.store.config.broker.prefetch_count
        )
        logger.info("Connected to broker")

    async def disconnect(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        await self.connection.close()
        logger.info("Broker connection closed")
