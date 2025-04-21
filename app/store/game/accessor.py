import logging
import typing
from collections.abc import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.game.models import (
    GameModel,
    GameParticipantModel,
    GameParticipantState,
    GameState,
    QuestionModel,
    UserModel,
)
from app.web.exceptions import (
    GameCreateError,
    ParticipantCreateError,
    ParticipantRegistrationError,
    QuestionCreateError,
    QuestionNotFoundError,
    UpdateGameStateError,
    UpdateStatusPlayerError,
    UserCreateError,
)

if typing.TYPE_CHECKING:
    from app.store.store import Store

logger = logging.getLogger(__name__)


class GameAccessor:
    def __init__(self, store: "Store") -> None:
        self.store = store

    async def create_game(
        self,
        chat_id: int,
        state: GameState,
        question_id: int,
    ) -> GameModel:
        async with self.store.database.session_maker() as session:
            game = GameModel(
                chat_id=chat_id, state=state, question_id=question_id
            )
            session.add(game)
            try:
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)
                raise GameCreateError(chat_id) from e
            return game

    async def update_game_state(self, game_id: int, state: GameState) -> None:
        async with self.store.database.session_maker() as session:
            game = await session.get(GameModel, game_id)
            game.state = state
            try:
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)
                raise UpdateGameStateError(game_id) from e

    async def get_running_game(self, chat_id: int) -> GameModel | None:
        async with self.store.database.session_maker() as session:
            stm = select(GameModel).options(
                joinedload(GameModel.current_player).joinedload(GameParticipantModel.user)
            ).where(
                and_(
                    GameModel.chat_id == chat_id,
                    GameModel.state != GameState.GAME_FINISHED,
                )
            )
            return await session.scalar(stm)

    async def get_game_by_game_id(self, game_id: int) -> GameModel:
        async with self.store.database.session_maker() as session:
            stm = (
                select(GameModel)
                .options(
                    joinedload(GameModel.question),
                    joinedload(GameModel.current_player).joinedload(
                        GameParticipantModel.user
                    ),
                )
                .where(GameModel.game_id == game_id)
            )
            result = await session.scalar(stm)
            return typing.cast(GameModel, result)

    async def update_revealed_letters(
        self, game: GameModel, letter: str
    ) -> None:
        async with self.store.database.session_maker() as session:
            game.revealed_letters += letter
            session.add(game)
            try:
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)

    async def set_current_player(
        self, game: GameModel, player: GameParticipantModel
    ) -> None:
        async with self.store.database.session_maker() as session:
            game.current_player = player
            session.add(game)
            try:
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)

    async def add_points_player(
        self,
        player: GameParticipantModel,
        points: int,
    ) -> None:
        async with self.store.database.session_maker() as session:
            player.points += points
            session.add(player)
            try:
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)

    async def create_questions(
        self, question: str, answer: str
    ) -> QuestionModel:
        async with self.store.database.session_maker() as session:
            question_model = QuestionModel(question=question, answer=answer)
            session.add(question_model)
            try:
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)
                raise QuestionCreateError(question, answer) from e
            return question_model

    async def get_random_question(self) -> QuestionModel:
        async with self.store.database.session_maker() as session:
            stm = select(QuestionModel).order_by(func.random()).limit(1)
            result = await session.execute(stm)
            try:
                return result.scalar_one()
            except NoResultFound as e:
                logger.error("There is no question in the DB")
                raise QuestionNotFoundError("The database is empty ") from e

    async def get_user_by_tg_id(self, tg_user_id: int) -> UserModel | None:
        async with self.store.database.session_maker() as session:
            return await session.scalar(
                select(UserModel).where(UserModel.tg_user_id == tg_user_id)
            )

    async def create_user(
        self,
        tg_user_id: int,
        username: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> UserModel:
        async with self.store.database.session_maker() as session:
            user = UserModel(
                tg_user_id=tg_user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(user)
            try:
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)
                raise UserCreateError(tg_user_id) from e
            return user

    async def create_game_participant(
        self,
        game_id: int,
        user_id: int,
        turn_order: int,
    ) -> GameParticipantModel:
        async with self.store.database.session_maker() as session:
            player = GameParticipantModel(
                game_id=game_id,
                user_id=user_id,
                turn_order=turn_order,
            )
            session.add(player)
            try:
                await session.commit()
            except IntegrityError as e:
                logger.warning("The participant is already registered")
                raise ParticipantRegistrationError(game_id, user_id) from e
            except SQLAlchemyError as e:
                logger.error(e)
                raise ParticipantCreateError(game_id, user_id) from e
            return player

    async def get_count_participant(self, game_id: int) -> int:
        async with self.store.database.session_maker() as session:
            stm = select(func.count(1)).where(
                GameParticipantModel.game_id == game_id
            )
            result = await session.scalar(stm)
            return typing.cast(int, result)

    async def get_players_by_game_id(
        self, game_id: int
    ) -> Sequence[GameParticipantModel]:
        async with self.store.database.session_maker() as session:
            stm = (
                select(GameParticipantModel)
                .options(joinedload(GameParticipantModel.user))
                .where(GameParticipantModel.game_id == game_id)
            )
            result = await session.scalars(stm)
            return result.all()

    async def get_active_player(
        self, game_id: int
    ) -> GameParticipantModel | None:
        async with self.store.database.session_maker() as session:
            stm = (
                select(GameParticipantModel)
                .options(joinedload(GameParticipantModel.user))
                .where(
                    and_(
                        GameParticipantModel.game_id == game_id,
                        GameParticipantModel.state
                        == GameParticipantState.ACTIVE_TURN,
                    )
                )
            )
            return await session.scalar(stm)

    async def update_status_player(
        self,
        player: GameParticipantModel,
        status: GameParticipantState,
    ) -> None:
        async with self.store.database.session_maker() as session:
            player.state = status
            session.add(player)
            try:
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)
                raise UpdateStatusPlayerError(
                    player.participant_id,
                    status,
                ) from e

    async def update_status_many_players(
        self,
        players: list[GameParticipantModel],
        status: GameParticipantState
    ) -> None:
        async with self.store.database.session_maker() as session:
            for p in players:
                p.state = status
            session.add_all(players)
            await session.commit()
