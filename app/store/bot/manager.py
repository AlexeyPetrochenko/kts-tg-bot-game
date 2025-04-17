import logging
import typing

from app.bot.handlers import (
    BaseHandler,
    JoinHandler,
    LeaveGameHandler,
    SayLetterHandler,
    SayWordHandler,
    StartHandler,
)
from app.bot.schemes import CallbackQuery, Message, Update

if typing.TYPE_CHECKING:
    from app.store.store import Store

logger = logging.getLogger(__name__)


class BotManager:
    def __init__(self, store: "Store"):
        self.store = store
        self.handlers: dict[str, BaseHandler] = {}

    def add_handler(self, command: str, handler: type[BaseHandler]) -> None:
        self.handlers[command] = handler(self.store)

    async def handle_updates(self, update: Update) -> None:
        if isinstance(update.body, CallbackQuery):
            command = self.handlers.get(update.body.command)
            await command.handle(update.body)
        elif isinstance(update.body, Message):
            await self.store.tg_api.send_button_start(update.body.chat_id)


def setup_bot_manager(store: "Store") -> BotManager:
    bot_manager = BotManager(store)
    bot_manager.add_handler("/start", StartHandler)
    bot_manager.add_handler("/join", JoinHandler)
    bot_manager.add_handler("/leave_game", LeaveGameHandler)
    bot_manager.add_handler("/say_letter", SayLetterHandler)
    bot_manager.add_handler("/say_word", SayWordHandler)
    return bot_manager
