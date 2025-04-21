import logging
import typing

from app.bot.handlers import (
    BaseHandler,
    JoinHandler,
    LeaveGameHandler,
    SayLetterHandler,
    SayWordHandler,
    StartHandler,
    TextMessageHandler,
)
from app.bot.schemes import CallbackQuery, Message, Update

if typing.TYPE_CHECKING:
    from app.store.store import Store

logger = logging.getLogger(__name__)


class BotManager:
    def __init__(self, store: "Store"):
        self.store = store
        self.handlers: dict[str, BaseHandler] = {}
        self.default_handler: TextMessageHandler | None = None

    def add_handler(self, command: str, handler: type[BaseHandler]) -> None:
        self.handlers[command] = handler(self.store)

    async def handle_updates(self, update: Update) -> None:
        if isinstance(update.body, CallbackQuery):
            handler = self.handlers.get(update.body.command)
            await handler(update.body)
        elif isinstance(update.body, Message):
            await self.default_handler.handle(update.body)

    def set_default_handler(self, handler: type[TextMessageHandler]) -> None:
        self.default_handler = handler(self.store)


def setup_bot_manager(store: "Store") -> BotManager:
    bot_manager = BotManager(store)
    bot_manager.add_handler("/start", StartHandler)
    bot_manager.add_handler("/join", JoinHandler)
    bot_manager.add_handler("/leave_game", LeaveGameHandler)
    bot_manager.add_handler("/say_letter", SayLetterHandler)
    bot_manager.add_handler("/say_word", SayWordHandler)
    bot_manager.set_default_handler(TextMessageHandler)
    return bot_manager
