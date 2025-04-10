import logging
import typing
from urllib.parse import urlencode

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.bot.poller import Poller
from app.bot.schemes import Message, Update

if typing.TYPE_CHECKING:
    from app.store.store import Store

API_PATH = "https://api.telegram.org/bot"
logger = logging.getLogger(__name__)


class TGApiAccessor:
    def __init__(self, store: "Store") -> None:
        self.store = store

        self.session: ClientSession | None = None
        self.poller: Poller | None = None
        self.timeout: int = 30
        self.offset: int | None = None

    async def connect(self) -> None:
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        self.poller = Poller(self.store)
        self.poller.start()
        logger.info("Polling started")

    async def disconnect(self) -> None:
        if self.poller:
            await self.poller.stop()
            logger.info("Poller Stopped")

        if not self.session.closed:
            await self.session.close()
            logger.info("Session closed")

    async def poll(self) -> None:
        async with self.session.get(
            self._build_query(
                API_PATH,
                self.store.config.bot.token,
                "getUpdates",
                params={"timeout": self.timeout, "offset": self.offset},
            )
        ) as response:
            updates = await response.json()
            for update_ in updates["result"]:
                # TODO: Вынести парсинг и обработку сообщения
                update = Update(
                    update_id=update_["update_id"],
                    message=Message(
                        message_id=update_["message"]["message_id"],
                        from_id=update_["message"]["from"]["id"],
                        from_name=update_["message"]["from"]["first_name"],
                        chat_id=update_["message"]["chat"]["id"],
                        text=update_["message"].get("text", "No text"),
                        date=update_["message"]["date"],
                    ),
                )
                await self.store.bot_manager.handle_updates(update)
                self.offset = update.update_id + 1

    @staticmethod
    def _build_query(host: str, token: str, method: str, params: dict) -> str:
        params = {k: v for k, v in params.items() if v is not None}
        return f"{host}{token}/{method}?{urlencode(params)}"

    async def send_message(self, message: Message) -> None:
        async with self.session.get(
            self._build_query(
                API_PATH,
                self.store.config.bot.token,
                "sendMessage",
                params={"chat_id": message.chat_id, "text": message.text},
            )
        ) as response:
            data = await response.json()
            logger.info(data)
