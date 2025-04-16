import logging
import typing

from app.game.models import GameModel, GameState
from app.game.states import BaseFsmState, PlayersWaitingFsmState

if typing.TYPE_CHECKING:
    from app.store.store import Store

logger = logging.getLogger(__name__)


class Fsm:
    def __init__(self, store: "Store", chat_id: int) -> None:
        self.store = store
        self.chat_id = chat_id
        self.states: dict[GameState, BaseFsmState] = {}
        self.current_state: BaseFsmState | None = None
        self.game_id: int | None = None

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
    return fsm
