import logging
import random
import typing
from abc import ABC, abstractmethod
from collections.abc import Sequence

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
        await self.fsm.store.game_accessor.update_game_state(
            self.fsm.game_id,
            GameState.NEXT_PLAYER_TURN,
        )
        logger.info("PlayersWaitingFsmState [EXIT]")

    async def update_(self) -> None:
        logger.info("PlayersWaitingFsmState [UPDATE]")
        count = await self.fsm.store.game_accessor.get_count_participant(
            self.fsm.game_id
        )
        if count >= NUMBER_OF_PARTICIPANTS:
            await self.fsm.set_current_state(GameState.NEXT_PLAYER_TURN)


class NextPlayerTurnFsmState(BaseFsmState):
    async def enter_(self) -> None:
        logger.info("NextPlayerTurnFsmState [ENTER]")
        players = await self.fsm.store.game_accessor.get_players_by_game_id(
            self.fsm.game_id
        )
        active_player = await self.fsm.store.game_accessor.get_active_player(
            self.fsm.game_id
        )
        await self._pass_turn(players, active_player)
        await self.fsm.set_current_state(GameState.PLAYER_TURN)

    async def exit_(self) -> None:
        await self.fsm.store.game_accessor.update_game_state(
            self.fsm.game_id,
            GameState.PLAYER_TURN,
        )
        logger.info("NextPlayerTurnFsmState [EXIT]")

    async def _pass_turn(
        self,
        players: Sequence[GameParticipantModel],
        active_player: GameParticipantModel | None = None,
    ) -> None:
        if active_player is None:
            next_active_player = random.choice(
                [p for p in players if p.state == GameParticipantState.WAITING]
            )
            await self.fsm.store.game_accessor.update_status_player(
                next_active_player,
                GameParticipantState.ACTIVE_TURN,
            )
            return

        next_active_player = self._determine_next_player(players, active_player)
        await self.fsm.store.game_accessor.update_status_player(
            active_player,
            GameParticipantState.WAITING,
        )
        await self.fsm.store.game_accessor.update_status_player(
            next_active_player,
            GameParticipantState.ACTIVE_TURN,
        )
        logger.info("Next turn player: %s", next_active_player)

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

    async def exit_(self) -> None:
        logger.info("PlayerTurnFsmState [EXIT]")
