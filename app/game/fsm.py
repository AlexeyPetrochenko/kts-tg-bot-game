import logging
import typing

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
from app.game.timer import FsmTimerManager
from app.poller.schemes import Message

if typing.TYPE_CHECKING:
    from app.store.store import Store

logger = logging.getLogger(__name__)


class Fsm:
    def __init__(
        self,
        store: "Store",
        chat_id: int,
        game_id: int,
        timer_manager: FsmTimerManager,
    ) -> None:
        self.store = store
        self.chat_id = chat_id
        self.game_id = game_id
        self.states: dict[GameState, BaseFsmState] = {}
        self.timer_manager = timer_manager
        self.current_state: BaseFsmState | None = None
        self.current_player_tg_id: int | None = None
        self.current_player_username: str | None = None
        self.bonus_points: int = 0

    async def restore_current_state(self, game: GameModel) -> None:
        self.current_state = self.states.get(game.state)
        self.bonus_points = game.bonus_points
        if game.state != GameState.WAITING_FOR_PLAYERS:
            self.current_player_tg_id = game.current_player.user.tg_user_id
            self.current_player_username = game.current_player.user.username
        await self.current_state.enter_()

    async def set_current_state(self, state: GameState) -> None:
        if self.current_state == self.states.get(state):
            return
        if self.current_state is not None:
            await self.current_state.exit_()
        await self.store.game_accessor.update_game_state(self.game_id, state)
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


def setup_fsm(store: "Store", chat_id: int, game_id: int) -> Fsm:
    fsm = Fsm(store, chat_id, game_id, FsmTimerManager())
    fsm.add_state(GameState.WAITING_FOR_PLAYERS, PlayersWaitingFsmState)
    fsm.add_state(GameState.NEXT_PLAYER_TURN, NextPlayerTurnFsmState)
    fsm.add_state(GameState.PLAYER_TURN, PlayerTurnFsmState)
    fsm.add_state(GameState.WAITING_FOR_LETTER, WaitingLetterFsmState)
    fsm.add_state(GameState.WAITING_FOR_WORD, WaitingWordFsmState)
    fsm.add_state(GameState.CHECK_WINNER, CheckWinnerFsmState)
    fsm.add_state(GameState.GAME_FINISHED, FinishGameFsmState)
    return fsm
