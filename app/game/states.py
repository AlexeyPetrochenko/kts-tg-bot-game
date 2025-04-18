import logging
import random
import typing
from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.bot.schemes import Message
from app.game.models import (
    GameParticipantModel,
    GameParticipantState,
    GameState,
)

if typing.TYPE_CHECKING:
    from app.game.fsm import Fsm

logger = logging.getLogger(__name__)
NUMBER_OF_PARTICIPANTS = 2


class BaseFsmState(ABC):
    def __init__(self, fsm: "Fsm", enum_sate: GameState) -> None:
        self.fsm = fsm
        self.enum_state = enum_sate

    @abstractmethod
    async def enter_(self) -> None:
        pass

    @abstractmethod
    async def exit_(self) -> None:
        pass

    @abstractmethod
    async def update_(self, context: Message | None = None) -> None:
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
        # await self.fsm.store.game_accessor.update_game_state(
        #     self.fsm.game_id,
        #     GameState.NEXT_PLAYER_TURN,
        # )
        logger.info("PlayersWaitingFsmState [EXIT]")

    async def update_(self, context: Message | None = None) -> None:
        logger.info("PlayersWaitingFsmState [UPDATE]")
        count = await self.fsm.store.game_accessor.get_count_participant(
            self.fsm.game_id
        )
        if count >= NUMBER_OF_PARTICIPANTS:
            await self.fsm.set_current_state(GameState.NEXT_PLAYER_TURN)


class NextPlayerTurnFsmState(BaseFsmState):
    async def enter_(self) -> None:
        logger.info("NextPlayerTurnFsmState [ENTER]")
        game = await self.fsm.store.game_accessor.get_game_by_game_id(
            self.fsm.game_id
        )
        players = await self.fsm.store.game_accessor.get_players_by_game_id(
            self.fsm.game_id
        )
        active_player = game.current_player
        next_active_player = await self._pass_turn(players, active_player)
        self.fsm.current_player_tg_id = next_active_player.user.tg_user_id
        await self.fsm.store.game_accessor.set_current_player(
            game, next_active_player
        )
        await self.fsm.set_current_state(GameState.PLAYER_TURN)

    async def exit_(self) -> None:
        # await self.fsm.store.game_accessor.update_game_state(
        #     self.fsm.game_id,
        #     GameState.PLAYER_TURN,
        # )
        logger.info("NextPlayerTurnFsmState [EXIT]")

    async def _pass_turn(
        self,
        players: Sequence[GameParticipantModel],
        active_player: GameParticipantModel | None = None,
    ) -> GameParticipantModel:
        if active_player is None:
            next_active_player = random.choice(
                [p for p in players if p.state == GameParticipantState.WAITING]
            )
            await self.fsm.store.game_accessor.update_status_player(
                next_active_player,
                GameParticipantState.ACTIVE_TURN,
            )
            return next_active_player

        next_active_player = self._determine_next_player(players, active_player)
        await self.fsm.store.game_accessor.update_status_player(
            active_player,
            GameParticipantState.WAITING,
        )
        await self.fsm.store.game_accessor.update_status_player(
            next_active_player,
            GameParticipantState.ACTIVE_TURN,
        )
        logger.info("Next turn player: %s", next_active_player.user.username)
        return next_active_player

    async def update_(self, context: Message | None = None) -> None:
        logger.info("NextPlayerTurnFsmState [UPDATE]")

    @staticmethod
    def _determine_next_player(
        players: Sequence[GameParticipantModel],
        active_player: GameParticipantModel,
    ) -> GameParticipantModel:
        players_in_order = sorted(players, key=lambda p: p.turn_order)
        idx = (active_player.turn_order + 1) % len(players)
        while players_in_order[idx].state != GameParticipantState.WAITING:
            idx = (idx + 1) % len(players)
        return players_in_order[idx]


class PlayerTurnFsmState(BaseFsmState):
    async def enter_(self) -> None:
        logger.info("PlayerTurnFsmState [ENTER]")
        active_player = await self.fsm.store.game_accessor.get_active_player(
            self.fsm.game_id
        )
        if active_player is None:
            await self.fsm.set_current_state(GameState.NEXT_PLAYER_TURN)

        game = await self.fsm.store.game_accessor.get_game_by_game_id(
            self.fsm.game_id
        )
        word = self.mask_word(game.question.answer, game.revealed_letters)
        self.fsm.bonus_points = self._spin_wheel()
        await self.fsm.store.tg_api.send_turn_buttons(
            self.fsm.chat_id,
            active_player.user.username,  # type: ignore[attr-defined]
            game.question.question,
            word,
            active_player.points,
            self.fsm.bonus_points,
        )

    async def exit_(self) -> None:
        logger.info("PlayerTurnFsmState [EXIT]")

    async def update_(self, context: Message | None = None) -> None:
        logger.info("PlayerTurnFsmState [UPDATE]")

    @staticmethod
    def mask_word(word: str, revealed_letters: str) -> str:
        letters = set(revealed_letters.upper())
        mask_word = []
        for letter in word.upper():
            if letter in letters:
                mask_word.append(letter)
            else:
                mask_word.append("_")
        return " ".join(mask_word)

    @staticmethod
    def _spin_wheel() -> int:
        points = [0, 100, 250, 350, 400, 450, 500, 600, 750, 1000]
        weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        return random.choices(points, weights=weights, k=1)[0]


class CheckWinnerFsmState(BaseFsmState):
    async def enter_(self) -> None:
        logger.info("CheckWinnerFsmState [ENTER]")

        # Проверка количества активных игроков
        players = await self.fsm.store.game_accessor.get_players_by_game_id(
            self.fsm.game_id
        )
        active_players = self._filter_active_players(players)
        if len(active_players) == 1:
            winner = active_players[0]
            await self.fsm.store.game_accessor.update_status_player(
                winner,
                GameParticipantState.WINNER,
            )
            await self.fsm.store.game_accessor.update_game_state(
                self.fsm.game_id,
                GameState.GAME_FINISHED,
            )
            await self.fsm.set_current_state(GameState.GAME_FINISHED)

    async def exit_(self) -> None:
        logger.info("CheckWinnerFsmState [EXIT]")

    async def update_(self, context: Message | None = None) -> None:
        pass

    @staticmethod
    def _filter_active_players(
        players: Sequence[GameParticipantModel],
    ) -> list[GameParticipantModel]:
        return [
            player
            for player in players
            if player.state
            in (GameParticipantState.ACTIVE_TURN, GameParticipantState.WAITING)
        ]


class FinishGameFsmState(BaseFsmState):
    async def enter_(self) -> None:
        logger.info("FinishGameFsmState [ENTER]")
        game = await self.fsm.store.game_accessor.get_game_by_game_id(
            self.fsm.game_id
        )
        players = await self.fsm.store.game_accessor.get_players_by_game_id(
            self.fsm.game_id
        )
        winner = [p for p in players if p.state == GameParticipantState.WINNER]
        losers = [p for p in players if p.state != GameParticipantState.WINNER]

        w = winner[0]
        winner_text = f"🏆 Победитель: @{w.user.username} с {w.points} очками"

        losers_sorted = sorted(losers, key=lambda p: p.points, reverse=True)
        losers_text = "\n\n💀 Проигравшие:\n"
        for i, p in enumerate(losers_sorted, start=1):
            losers_text += f"{i}. @{p.user.username} — {p.points} очков\n"
        text = (
            f"🎯 Игра завершена!\n"
            f"Слово: {game.question.answer.upper()}\n\n"
            f"{winner_text}"
            f"{losers_text}"
        )
        await self.fsm.store.tg_api.send_message(self.fsm.chat_id, text)
        self.fsm.store.fsm_manager.remove_fsm(self.fsm.chat_id)

    async def exit_(self) -> None:
        logger.info("FinishGameFsmState [EXIT]")

    async def update_(self, context: Message | None = None) -> None:
        pass


class WaitingLetterFsmState(BaseFsmState):
    async def enter_(self) -> None:
        logger.info("WaitingLetterFsmState [ENTER]")

    async def exit_(self) -> None:
        logger.info("WaitingLetterFsmState [EXIT]")

    async def send_message(self, base_text: str, text: str) -> None:
        await self.fsm.store.tg_api.send_message(
            self.fsm.chat_id, f"{base_text}\n{text}"
        )

    async def update_(self, context: Message | None = None) -> None:
        logger.info("WaitingLetterFsmState [UPDATE]")

        letter = context.text.upper()
        game = await self.fsm.store.game_accessor.get_game_by_game_id(
            self.fsm.game_id
        )
        player = game.current_player
        base_text = f"@{player.user.username} назвал букву: {letter}"

        # TODO: Неверный формат
        if len(letter) != 1 or not letter.isalpha():
            await self.send_message(base_text, "Это не буква!")
            await self.fsm.set_current_state(GameState.NEXT_PLAYER_TURN)
            return

        # TODO: Такую букву уже называли
        if letter in game.revealed_letters.upper():
            await self.send_message(base_text, "Такую букву уже называли!")
            await self.fsm.set_current_state(GameState.NEXT_PLAYER_TURN)
            return

        # TODO: Неверная буква
        if letter not in game.question.answer.upper():
            await self.send_message(base_text, "Такой буквы нет в слове")
            await self.fsm.store.game_accessor.update_revealed_letters(
                game,
                letter,
            )
            await self.fsm.set_current_state(GameState.NEXT_PLAYER_TURN)
            return

        # TODO: Буква названа верно
        await self.send_message(base_text, "Верно!")
        await self.fsm.store.game_accessor.update_revealed_letters(
            game,
            letter,
        )
        # TODO: Начисляем очки и снова ходим
        await self.fsm.store.game_accessor.add_points_player(
            player,
            self.fsm.bonus_points,
        )
        # TODO: Проверяем отгадано ли слово
        if self.is_word_guessed(game.question.answer, game.revealed_letters):
            await self.fsm.store.game_accessor.update_status_player(
                player,
                GameParticipantState.WINNER,
            )
            await self.fsm.set_current_state(GameState.GAME_FINISHED)
            return
        # TODO: Если не отгадано ходит снова
        await self.fsm.set_current_state(GameState.PLAYER_TURN)

    @staticmethod
    def is_word_guessed(word: str, revealed_letters: str) -> bool:
        word_letters = {ch.upper() for ch in word if ch.isalpha()}
        revealed_set = set(revealed_letters.upper())
        return word_letters.issubset(revealed_set)


class WaitingWordFsmState(BaseFsmState):
    async def enter_(self) -> None:
        pass

    async def exit_(self) -> None:
        pass

    async def update_(self, context: Message | None = None) -> None:
        pass
