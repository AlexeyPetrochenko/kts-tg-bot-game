import logging
import typing
from abc import ABC, abstractmethod

from app.game.models import GameState

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from app.game.fsm import Fsm


class BaseFsmState(ABC):
    def __init__(self, fsm: "Fsm") -> None:
        self.fsm = fsm

    @abstractmethod
    async def enter_(self) -> None:
        pass

    @abstractmethod
    async def exit_(self) -> None:
        pass


class PlayersWaitingFsmState(BaseFsmState):
    async def enter_(self) -> None:
        logger.info("PlayersWaitingFsmState [ENTER]")
        question = await self.fsm.store.game_accessor.get_random_question()
        game = await self.fsm.store.game_accessor.create_game(
            chat_id=self.fsm.chat_id,
            question_id=question.question_id,
            state=GameState.WAITING_FOR_PLAYERS,
        )
        self.fsm.game_id = game.game_id
        await self.fsm.store.tg_api.send_button_join(self.fsm.chat_id)

    async def exit_(self) -> None:
        logger.info("PlayersWaitingFsmState [EXIT]")

    async def update_(self) -> None:
        count = await self.fsm.store.game_accessor.get_count_participant(
            self.fsm.game_id
        )

        if count >= 2:
            # TODO: Написать состояние START_GAME
            # await self.fsm.set_current_state(GameState.START_GAME)
            logger.info("START_GAME [ENTER]")
