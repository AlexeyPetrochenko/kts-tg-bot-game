import enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.store.database.sqlalchemy_base import BaseModel


class GameState(enum.StrEnum):
    WAITING_FOR_GAME = "waiting_for_game"
    WAITING_FOR_PLAYERS = "waiting_for_players"
    START_GAME = "start_game"
    PLAYER_TURN = "player_turn"
    PLAYER_TURN_LETTER = "player_turn_letter"
    PLAYER_TURN_WORD = "player_turn_word"
    NEXT_PLAYER_TURN = "next_player_turn"
    GAME_FINISHED = "game_finished"


class GameParticipantState(enum.StrEnum):
    ACTIVE_TURN = "active_turn"
    WAITING = "waiting"
    WINNER = "winner"
    LOSER = "loser"
    LEFT = "left"


class GameModel(BaseModel):
    __tablename__ = "games"

    game_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    chat_id: Mapped[int]
    state: Mapped[GameState] = mapped_column(
        default=GameState.WAITING_FOR_PLAYERS
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.question_id")
    )
    revealed_letter: Mapped[str] = mapped_column(default="")

    question: Mapped["QuestionModel"] = relationship()
    game_participants: Mapped[list["GameParticipantModel"]] = relationship(
        back_populates="game",
        cascade="all, delete-orphan",
    )


class UserModel(BaseModel):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tg_user_id: Mapped[int]
    username: Mapped[str]
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]

    game_participations: Mapped[list["GameParticipantModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class GameParticipantModel(BaseModel):
    __tablename__ = "game_participants"

    participant_id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.game_id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE")
    )
    state: Mapped[GameParticipantState] = mapped_column(
        default=GameParticipantState.WAITING,
    )
    turn_order: Mapped[int | None]
    points: Mapped[int] = mapped_column(default=0)

    game: Mapped["GameModel"] = relationship(
        back_populates="game_participants",
    )
    user: Mapped["UserModel"] = relationship(
        back_populates="game_participations",
    )


class QuestionModel(BaseModel):
    __tablename__ = "questions"

    question_id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str]
    answer: Mapped[str]
