import logging
import typing
from abc import ABC, abstractmethod

from app.bot.schemes import Message

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from app.game.fsm import Fsm


class BaseFsmState(ABC):
    def __init__(self, fsm: "Fsm") -> None:
        self.fsm = fsm

    @abstractmethod
    async def _enter(self, message: Message) -> None:
        pass

    @abstractmethod
    async def _exit(self, message: Message) -> None:
        pass


class PlayersWaitingFsmState(BaseFsmState):
    async def _enter(self, message: Message) -> None:
        logger.info(message.text)
        logger.info("PlayersWaitingFsmState [ENTER]")

    async def _exit(self, message: Message) -> None:
        logger.info(message.text)
        logger.info("PlayersWaitingFsmState [EXIT]")
