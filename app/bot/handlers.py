import logging
from abc import ABC, abstractmethod

from app.bot.schemes import CallbackQuery
from app.game.models import GameState
from app.store.store import Store
from app.web.exceptions import ParticipantRegistrationError

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    def __init__(self, store: Store) -> None:
        self.store = store

    @abstractmethod
    async def handle(self, message: CallbackQuery) -> None:
        pass


class StartHandler(BaseHandler):
    async def handle(self, callback: CallbackQuery) -> None:
        if self.store.fsm_manager.get_fsm(callback.chat_id):
            await self.store.tg_api.answer_callback(
                callback.callback_id,
                "Игра уже запущена",
            )
            return

        game = await self.store.game_accessor.get_running_game(callback.chat_id)
        fsm = self.store.fsm_manager.set_fsm(callback.chat_id)

        if game:
            logger.info("Restoring the game")
            await self.store.tg_api.answer_callback(
                callback.callback_id,
                "Игра восстановлена",
            )
            await fsm.restore_current_state(game)
        else:
            logger.info("Starting new game")
            await fsm.set_current_state(GameState.WAITING_FOR_PLAYERS)
            await self.store.tg_api.answer_callback(
                callback.callback_id,
                "Старт игры",
            )


class JoinHandler(BaseHandler):
    async def handle(self, callback: CallbackQuery) -> None:
        fsm = self.store.fsm_manager.get_fsm(callback.chat_id)
        if fsm is None:
            await self.store.tg_api.answer_callback(
                callback.callback_id,
                "Нет активной игры",
            )
            return
        user = await self.store.game_accessor.get_user_by_tg_id(
            callback.from_id
        )
        if user is None:
            user = await self.store.game_accessor.create_user(
                callback.from_id, callback.from_username
            )
        player_count = await self.store.game_accessor.get_count_participant(
            game_id=fsm.game_id
        )
        try:
            await self.store.game_accessor.create_game_participant(
                fsm.game_id, user.user_id, player_count
            )
            await fsm.update_current_state()
            await self.store.tg_api.answer_callback(
                callback.callback_id,
                f"игрок {callback.from_username} присоединился к игре",
            )
        except ParticipantRegistrationError as e:
            logger.warning(e)
            await self.store.tg_api.answer_callback(
                callback.callback_id,
                f"{callback.from_username} - вы уже зарегистрированы",
            )
