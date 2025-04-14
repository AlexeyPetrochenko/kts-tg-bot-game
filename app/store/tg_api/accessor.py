import logging
import typing
from urllib.parse import urlencode

from aiohttp import ClientConnectionError, ClientResponseError, TCPConnector
from aiohttp.client import ClientSession

from app.bot.schemes import Message, Update

if typing.TYPE_CHECKING:
    from app.store.store import Store

API_PATH = "https://api.telegram.org/bot"
logger = logging.getLogger(__name__)


class TGApiAccessor:
    def __init__(self, store: "Store") -> None:
        self.store = store

        self.session: ClientSession | None = None
        self.timeout: int = 30
        self.offset: int | None = None

    async def connect(self) -> None:
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))

    async def disconnect(self) -> None:
        if not self.session.closed:
            await self.session.close()
            logger.info("Session closed")

    async def poll(self) -> None:
        params = {"timeout": self.timeout, "offset": self.offset}
        updates = await self._request_api("getUpdates", params)
        for update in updates["result"]:
            update_scheme = self._parse_message(update)
            if isinstance(update_scheme, Update):
                await self.store.bot_manager.handle_updates(update_scheme)
                self.offset = update_scheme.update_id + 1
            else:
                self.offset = update_scheme + 1

    async def send_message(self, message: Message) -> None:
        params = {"chat_id": message.chat_id, "text": message.text}
        await self._request_api("sendMessage", params)

    @staticmethod
    def _build_query(host: str, token: str, method: str, params: dict) -> str:
        params = {k: v for k, v in params.items() if v is not None}
        return f"{host}{token}/{method}?{urlencode(params)}"

    async def _request_api(self, method: str, params: dict) -> dict:
        try:
            async with self.session.get(
                self._build_query(
                    API_PATH, self.store.config.bot.token, method, params
                )
            ) as response:
                response.raise_for_status()
                return await response.json()
        except ClientConnectionError as e:
            logger.error(e)
            raise
        except ClientResponseError as e:
            logger.error(e)
            raise

    def _parse_message(self, update: dict) -> Update | int:
        try:
            return Update(
                update_id=update["update_id"],
                message=Message(
                    message_id=update["message"]["message_id"],
                    from_id=update["message"]["from"]["id"],
                    from_name=update["message"]["from"]["first_name"],
                    chat_id=update["message"]["chat"]["id"],
                    text=update["message"]["text"],
                    date=update["message"]["date"],
                ),
            )
        except KeyError as e:
            logger.error(
                "An update with an incorrect structure was missed. [%s]", e
            )
            return update["update_id"]
