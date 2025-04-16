import logging
import typing

from app.game.models import GameModel, GameState
from app.game.states import (
    BaseFsmState,
    NextPlayerTurnFsmState,
    PlayersWaitingFsmState,
    PlayerTurnFsmState,
)
from app.web.exceptions import FsmError

if typing.TYPE_CHECKING:
    from app.store.store import Store

logger = logging.getLogger(__name__)


class Fsm:
    def __init__(self, store: "Store", chat_id: int) -> None:
        self.store = store
        self.chat_id = chat_id
        self.states: dict[GameState, BaseFsmState] = {}
        self.current_state: BaseFsmState | None = None
        self._game_id: int | None = None

    @property
    def game_id(self) -> int:
        if self._game_id is None:
            # TODO: Что бы mypy не ругался, что может быть None
            # TODO: Возможно реализовать логику удаления fsm
            raise FsmError("Well, I managed to get the game state.")
        return self._game_id

    @game_id.setter
    def game_id(self, id_: int) -> None:
        self._game_id = id_

    async def restore_current_state(self, game: GameModel) -> None:
        # TODO: Написать логику по восстановлению игры из БД
        self.game_id = game.game_id
        self.current_state = self.states.get(game.state)
        logger.info("Тут будет логика по восстановлению игры")

    async def set_current_state(self, state: GameState) -> None:
        if self.current_state == self.states.get(state):
            return
        if self.current_state is not None:
            await self.current_state.exit_()
        self.current_state = self.states[state]
        await self.current_state.enter_()

    async def update_current_state(self) -> None:
        await self.current_state.update_()

    def add_state(
        self, name_state: GameState, state: type[BaseFsmState]
    ) -> None:
        self.states[name_state] = state(self)


def setup_fsm(store: "Store", chat_id: int) -> Fsm:
    fsm = Fsm(store, chat_id)
    fsm.add_state(GameState.WAITING_FOR_PLAYERS, PlayersWaitingFsmState)
    fsm.add_state(GameState.NEXT_PLAYER_TURN, NextPlayerTurnFsmState)
    fsm.add_state(GameState.PLAYER_TURN, PlayerTurnFsmState)
    return fsm
