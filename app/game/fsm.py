import logging
import typing

from app.bot.schemes import Message
from app.game.models import GameModel, GameState
from app.game.states import (
    BaseFsmState,
    CheckWinnerFsmState,
    FinishGameFsmState,
    NextPlayerTurnFsmState,
    PlayersWaitingFsmState,
    PlayerTurnFsmState,
    WaitingLetterFsmState,
    WaitingWordFsmState,
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
        self.current_player_tg_id: int | None = None
        self._game_id: int | None = None
        self.bonus_points: int = 0

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
        self.game_id = game.game_id
        if game.state == GameState.WAITING_FOR_PLAYERS:
            self.current_state = self.states.get(game.state)
            await self.update_current_state()
            if game.state == GameState.WAITING_FOR_PLAYERS:
                await self.store.tg_api.send_button_join(self.chat_id)
            return
        if game.state == GameState.PLAYER_TURN:
            player = await self.store.game_accessor.get_active_player(
                game.game_id
            )
            self.current_player_tg_id = player.user.tg_user_id

        await self.set_current_state(game.state)

    async def set_current_state(self, state: GameState) -> None:
        if self.current_state == self.states.get(state):
            return
        if self.current_state is not None:
            await self.current_state.exit_()
        try:
            await self.store.game_accessor.update_game_state(
                self.game_id, state
            )
        except FsmError:
            logger.info("The status has not yet been determined.")
        self.current_state = self.states[state]
        await self.current_state.enter_()

    async def update_current_state(
        self, context: Message | None = None
    ) -> None:
        await self.current_state.update_(context)

    def add_state(
        self, name_state: GameState, state: type[BaseFsmState]
    ) -> None:
        self.states[name_state] = state(self, name_state)


def setup_fsm(store: "Store", chat_id: int) -> Fsm:
    fsm = Fsm(store, chat_id)
    fsm.add_state(GameState.WAITING_FOR_PLAYERS, PlayersWaitingFsmState)
    fsm.add_state(GameState.NEXT_PLAYER_TURN, NextPlayerTurnFsmState)
    fsm.add_state(GameState.PLAYER_TURN, PlayerTurnFsmState)
    fsm.add_state(GameState.WAITING_FOR_LETTER, WaitingLetterFsmState)
    fsm.add_state(GameState.WAITING_FOR_WORD, WaitingWordFsmState)
    fsm.add_state(GameState.CHECK_WINNER, CheckWinnerFsmState)
    fsm.add_state(GameState.GAME_FINISHED, FinishGameFsmState)
    return fsm
