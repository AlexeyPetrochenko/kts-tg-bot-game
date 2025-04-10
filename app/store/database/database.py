import logging
import typing

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.store.database.sqlalchemy_base import BaseModel

if typing.TYPE_CHECKING:
    from app.store.store import Store


logger = logging.getLogger(__name__)


class Database:
    def __init__(self, store: "Store") -> None:
        self.store = store
        self.engine: AsyncEngine | None = None
        self._db: type[DeclarativeBase] = BaseModel
        self.session: async_sessionmaker[AsyncSession] | None = None

    async def connect(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        self.engine = create_async_engine(
            self.store.config.database.DATABASE_URL
        )
        self.session = async_sessionmaker(
            bind=self.engine, expire_on_commit=False
        )
        logger.info("Connection to the database")

    async def disconnect(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        await self.engine.dispose()
        logger.info("The connection to the database was disconnect")
