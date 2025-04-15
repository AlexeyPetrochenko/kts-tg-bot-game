import typing

from app.bot.schemes import Message
from app.game.models import GameState
from app.game.states import BaseFsmState, PlayersWaitingFsmState

if typing.TYPE_CHECKING:
    from app.store.game.fsm_manager import FsmManager


class Fsm:
    states: dict[GameState, BaseFsmState] = {}
    current_state: BaseFsmState | None = None

    def __init__(self, fsm_manager: "FsmManager") -> None:
        self.fsm_manager = fsm_manager

    async def set_current_state(
        self, state: GameState, message: Message
    ) -> None:
        if self.current_state is not None:
            await self.current_state._exit(message)
        self.current_state = self.states[state]
        await self.current_state._enter(message)

    def add_state(
        self, name_state: GameState, state: type[BaseFsmState]
    ) -> None:
        self.states[name_state] = state(self)


def setup_fsm(fsm_manager: "FsmManager") -> Fsm:
    fsm = Fsm(fsm_manager)
    fsm.add_state(GameState.WAITING_FOR_PLAYERS, PlayersWaitingFsmState)
    return fsm
