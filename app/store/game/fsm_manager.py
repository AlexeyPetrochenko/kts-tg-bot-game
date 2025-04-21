import typing

from app.game.fsm import Fsm, setup_fsm

if typing.TYPE_CHECKING:
    from app.store.store import Store


class FsmManager:
    def __init__(self, store: "Store") -> None:
        self.store = store
        self.fsm_storage: dict[int, Fsm] = {}

    def get_fsm(self, chat_id: int) -> Fsm | None:
        return self.fsm_storage.get(chat_id)

    def set_fsm(self, chat_id: int, game_id: int) -> Fsm:
        fsm = setup_fsm(self.store, chat_id, game_id)
        self.fsm_storage[chat_id] = fsm
        return fsm

    def remove_fsm(self, chat_id: int) -> None:
        if chat_id in self.fsm_storage:
            del self.fsm_storage[chat_id]
