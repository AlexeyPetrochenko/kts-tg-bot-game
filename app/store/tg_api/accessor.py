import logging
import typing

from aiohttp import ClientConnectionError, ClientResponseError, TCPConnector
from aiohttp.client import ClientSession

if typing.TYPE_CHECKING:
    from app.store.store import Store

API_PATH = "https://api.telegram.org/bot"
logger = logging.getLogger(__name__)


class TGApiAccessor:
    def __init__(self, store: "Store") -> None:
        self.store = store
        self.session: ClientSession | None = None

    async def connect(self) -> None:
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))

    async def disconnect(self) -> None:
        if not self.session.closed:
            await self.session.close()
            logger.info("Session closed")

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

    async def fetch_updates(self, offset: int | None, timeout_: int) -> dict:
        params = {
            "timeout": timeout_,
            "offset": offset,
            "allowed_updates": ["message", "callback_query"],
        }
        return await self._request_api("getUpdates", params)

    async def send_message(self, chat_id: int, text: str) -> None:
        params = {"chat_id": chat_id, "text": text}
        await self._request_api("sendMessage", params)

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

    async def send_turn_buttons(
        self,
        chat_id: int,
        username: str,
        question: str,
        word: str,
        user_points: int,
        bonus_points: int,
    ) -> None:
        text = f"""
            Ходит: {username}
            Ваши очки: {user_points}
            Вопрос: {question}
            Слово: {word}
            Сектор: {bonus_points} очков на барабане
            """
        reply_markup = {
            "inline_keyboard": [
                [{"text": "Покинуть игру", "callback_data": "/leave_game"}],
                [{"text": "Назвать букву", "callback_data": "/say_letter"}],
                [{"text": "Назвать слово", "callback_data": "/say_word"}],
            ]
        }
        params = {
            "chat_id": chat_id,
            "text": text,
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
