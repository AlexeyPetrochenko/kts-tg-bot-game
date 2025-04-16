import logging
import typing

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError

from app.game.models import (
    GameModel,
    GameParticipantModel,
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

    async def get_running_game(self, chat_id: int) -> GameModel | None:
        async with self.store.database.session_maker() as session:
            stm = select(GameModel).where(
                and_(
                    GameModel.chat_id == chat_id,
                    GameModel.state != GameState.GAME_FINISHED,
                )
            )
            return await session.scalar(stm)

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
            stm = select(func.count(GameParticipantModel.participant_id)).where(
                GameParticipantModel.game_id == game_id
            )
            result = await session.scalar(stm)
            return result or 0
