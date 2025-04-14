import logging
import typing

from app.bot.handlers import BaseHandler, StartHandler
from app.bot.schemes import Update

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
        logger.info(update)
        command = self.handlers.get(update.message.text.split()[0])
        if command:
            await command.handle(update.message)
        else:
            logger.info("Unknown command - [%s]", update.message.text)
            await self.store.tg_api.send_message(update.message)


def setup_bot_manager(store: "Store") -> BotManager:
    bot_manager = BotManager(store)
    bot_manager.add_handler("/start", StartHandler)
    return bot_manager
