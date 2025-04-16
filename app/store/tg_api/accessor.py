import logging
import typing

from aiohttp import ClientConnectionError, ClientResponseError, TCPConnector
from aiohttp.client import ClientSession

from app.bot.schemes import CallbackQuery, Message, Update

if typing.TYPE_CHECKING:
    from app.store.store import Store

API_PATH = "https://api.telegram.org/bot"
MAX_CALLBACK_AGE = 30
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
        params = {
            "timeout": self.timeout,
            "offset": self.offset,
            "allowed_updates": ["message", "callback_query"],
        }
        updates = await self._request_api("getUpdates", params)
        for update in updates["result"]:
            update_scheme = self._parse_update(update)
            if isinstance(update_scheme, Update):
                await self.store.bot_manager.handle_updates(update_scheme)
                self.offset = update_scheme.update_id + 1
            else:
                self.offset = update_scheme + 1

    async def send_echo_message(self, message: Message) -> None:
        params = {"chat_id": message.chat_id, "text": message.text}
        await self._request_api("sendMessage", params)

    # TODO: Возможно создать один метод для кнопок и dict с наполнением
    async def send_button_start(self, chat_id: int) -> None:
        reply_markup = {
            "inline_keyboard": [
                [{"text": "Начать игру", "callback_data": "/start"}]
            ]
        }
        params = {
            "chat_id": chat_id,
            "text": "Запустить игру?",
            "reply_markup": reply_markup,
        }
        await self._request_api("sendMessage", params)

    async def send_button_join(self, chat_id: int) -> None:
        reply_markup = {
            "inline_keyboard": [
                [{"text": "Присоединиться", "callback_data": "/join"}]
            ]
        }
        params = {
            "chat_id": chat_id,
            "text": "Присоединиться к игре?",
            "reply_markup": reply_markup,
        }
        await self._request_api("sendMessage", params)

    async def answer_callback(
        self, callback_id: str, text: str | None = None
    ) -> None:
        params = {"callback_query_id": callback_id, "text": text}
        try:
            await self._request_api("answerCallbackQuery", params)
        except ClientResponseError:
            logger.warning("The callback response time has expired.")

    async def _request_api(self, method: str, params: dict) -> dict:
        try:
            url = f"{API_PATH}{self.store.config.bot.token}/{method}"
            async with self.session.post(url=url, json=params) as response:
                response.raise_for_status()
                return await response.json()
        except ClientConnectionError as e:
            logger.error(e)
            raise
        except ClientResponseError as e:
            logger.error(e)
            raise

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
                            "username"
                        ],
                    ),
                )

            return Update(
                update_id=update["update_id"],
                date=update["message"]["date"],
                body=Message(
                    chat_id=update["message"]["chat"]["id"],
                    text=update["message"]["text"],
                    message_id=update["message"]["message_id"],
                    from_id=update["message"]["from"]["id"],
                    from_username=update["message"]["from"]["first_name"],
                ),
            )

        except KeyError as e:
            logger.error(
                "An update with an incorrect structure was missed. [%s]", e
            )
        return update["update_id"]
