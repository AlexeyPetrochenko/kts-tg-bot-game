import logging
from abc import ABC, abstractmethod

from app.bot.schemes import Message
from app.game.models import GameState
from app.store.store import Store

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    def __init__(self, store: Store) -> None:
        self.store = store

    @abstractmethod
    async def handle(self, message: Message) -> None:
        pass


class StartHandler(BaseHandler):
    async def handle(self, message: Message) -> None:
        logger.info("start handler, %s", message)
        fsm = self.store.fsm_manager.set_fsm(message.chat_id)
        await fsm.set_current_state(GameState.WAITING_FOR_PLAYERS, message)
