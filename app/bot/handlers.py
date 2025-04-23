import logging
from abc import ABC, abstractmethod

from app.game.models import GameParticipantState, GameState
from app.poller.schemes import CallbackQuery, Message
from app.store.store import Store
from app.web.exceptions import ParticipantRegistrationError

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    def __init__(self, store: Store) -> None:
        self.store = store

    @abstractmethod
    async def handle(self, callback: CallbackQuery) -> None:
        pass

    async def __call__(self, callback: CallbackQuery) -> None:
        self.save_log(callback)
        await self.handle(callback)

    def save_log(self, callback: CallbackQuery) -> None:
        logger.info(
            "%s: User %s, clicked button %s, in chat_id: %s",
            self.__class__.__name__,
            callback.from_username,
            callback.command,
            callback.chat_id,
        )

    async def answer_callback(self, callback: CallbackQuery, text: str) -> None:
        await self.store.tg_api.answer_callback(callback.callback_id, text)


class StartHandler(BaseHandler):
    async def handle(self, callback: CallbackQuery) -> None:
        # TODO: Проверяем нет ли запущенной игры
        if self.store.fsm_manager.get_fsm(callback.chat_id):
            await self.answer_callback(callback, "Игра уже запущена")
            return

        # TODO: Проверяем нет ли незавершенных игр
        game = await self.store.game_accessor.get_running_game(callback.chat_id)
        if game:
            fsm = self.store.fsm_manager.set_fsm(callback.chat_id, game.game_id)
            logger.info(
                "Restoring the game_id: %s in chat_id: %s",
                game.game_id,
                game.chat_id,
            )
            await self.answer_callback(callback, "Игра восстановлена")
            await fsm.restore_current_state(game)
        else:
            question = await self.store.game_accessor.get_random_question()
            game = await self.store.game_accessor.create_game(
                chat_id=callback.chat_id,
                question_id=question.question_id,
                state=GameState.WAITING_FOR_PLAYERS,
            )
            logger.info("Starting new game in chat_id: %s", game.chat_id)
            fsm = self.store.fsm_manager.set_fsm(callback.chat_id, game.game_id)
            await self.answer_callback(callback, "Старт игры")
            await fsm.set_current_state(GameState.WAITING_FOR_PLAYERS)


class JoinHandler(BaseHandler):
    async def handle(self, callback: CallbackQuery) -> None:
        # TODO: Проверяем есть ли активная игра
        fsm = self.store.fsm_manager.get_fsm(callback.chat_id)
        if fsm is None:
            await self.answer_callback(callback, "Нет активной игры")
            return

        # TODO: Проверяем state
        if fsm.current_state.enum_state != GameState.WAITING_FOR_PLAYERS:
            await self.answer_callback(callback, "Игра на другом этапе")
            return

        # TODO: Добавляем пользователя в таблицу User если его еще там нет
        user = await self.store.game_accessor.get_user_by_tg_id(
            callback.from_id
        )
        if user is None:
            user = await self.store.game_accessor.create_user(
                callback.from_id, callback.from_username
            )
        # TODO: Назначаем ему порядковый номер для хода и добавляем в игру
        player_count = await self.store.game_accessor.get_count_participant(
            game_id=fsm.game_id
        )
        try:
            await self.store.game_accessor.create_game_participant(
                fsm.game_id, user.user_id, player_count
            )
            await self.answer_callback(
                callback,
                f"Игрок @{callback.from_username} присоединился к игре",
            )

            await fsm.update_current_state()

        except ParticipantRegistrationError as e:
            logger.warning(e)
            await self.answer_callback(
                callback,
                f"{callback.from_username} - вы уже зарегистрированы",
            )


class LeaveGameHandler(BaseHandler):
    async def handle(self, callback: CallbackQuery) -> None:
        # TODO: Проверяем есть ли запущенная игра
        fsm = self.store.fsm_manager.get_fsm(callback.chat_id)
        if fsm is None:
            await self.answer_callback(callback, "Нет активной игры")
            return

        # TODO: Проверяем state
        if fsm.current_state.enum_state != GameState.PLAYER_TURN:
            await self.answer_callback(callback, "Игра на другом этапе")
            return

        # TODO: Проверяем ход пользователя
        if callback.from_id != fsm.current_player_tg_id:
            await self.answer_callback(callback, "Дождитесь своего хода")
            return

        # TODO: меняем статус на LEFT
        game = await self.store.game_accessor.get_game_by_game_id(fsm.game_id)
        await self.answer_callback(callback, "Вы покинули игру")
        await self.store.tg_api.send_message(
            fsm.chat_id, f"@{game.current_player.user.username} Покинул игру"
        )
        await self.store.game_accessor.update_status_player(
            game.current_player,
            GameParticipantState.LEFT,
        )
        await fsm.set_current_state(GameState.CHECK_WINNER)


class SayLetterHandler(BaseHandler):
    async def handle(self, callback: CallbackQuery) -> None:
        # TODO: Проверяем есть ли запущенная игра
        fsm = self.store.fsm_manager.get_fsm(callback.chat_id)
        if fsm is None:
            await self.answer_callback(callback, "Нет активной игры")
            return

        # TODO: Проверяем state
        if fsm.current_state.enum_state != GameState.PLAYER_TURN:
            await self.answer_callback(callback, "Игра на другом этапе")
            return

        # TODO: Проверяем ход пользователя
        if callback.from_id != fsm.current_player_tg_id:
            await self.answer_callback(callback, "Дождитесь своего хода")
            return

        await self.answer_callback(callback, "Введи одну букву")
        # await self.store.tg_api.send_message(
        #     callback.chat_id, f"@{callback.from_username} Ждем букву!"
        # )
        # Делаем переход в состояние WAITING_FOR_LETTER
        await fsm.set_current_state(GameState.WAITING_FOR_LETTER)


class SayWordHandler(BaseHandler):
    async def handle(self, callback: CallbackQuery) -> None:
        # TODO: Проверяем есть ли запущенная игра
        fsm = self.store.fsm_manager.get_fsm(callback.chat_id)
        if fsm is None:
            await self.answer_callback(callback, "Нет активной игры")
            return

        # TODO: Проверяем state
        if fsm.current_state.enum_state != GameState.PLAYER_TURN:
            await self.answer_callback(callback, "Игра на другом этапе")
            return

        # TODO: Проверяем ход пользователя
        if callback.from_id != fsm.current_player_tg_id:
            await self.answer_callback(callback, "Дождитесь своего хода")
            return
        await self.answer_callback(callback, "Введи слово")
        # await self.store.tg_api.send_message(
        #     callback.chat_id, f"@{callback.from_username} Ждем слово!"
        # )
        # Делаем переход в состояние WAITING_FOR_WORD
        await fsm.set_current_state(GameState.WAITING_FOR_WORD)


class TextMessageHandler:
    def __init__(self, store: Store) -> None:
        self.store = store

    async def handle(self, message: Message) -> None:
        # TODO: Проверяем есть ли запущенная игра
        fsm = self.store.fsm_manager.get_fsm(message.chat_id)
        if fsm is None:
            await self.store.tg_api.send_button_start(message.chat_id)
            return

        # Проверяем букву
        if fsm.current_state.enum_state == GameState.WAITING_FOR_LETTER:
            await fsm.update_current_state(message)
            return

        # Проверяем слово
        if fsm.current_state.enum_state == GameState.WAITING_FOR_WORD:
            await fsm.update_current_state(message)
            return
