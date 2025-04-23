import enum

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.store.database.sqlalchemy_base import BaseModel


class GameState(enum.StrEnum):
    WAITING_FOR_PLAYERS = "waiting_for_players"
    PLAYER_TURN = "player_turn"
    NEXT_PLAYER_TURN = "next_player_turn"
    WAITING_FOR_LETTER = "waiting_for_letter"
    WAITING_FOR_WORD = "waiting_for_word"
    CHECK_WINNER = "check_winner"
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
    chat_id: Mapped[int] = mapped_column(BigInteger)
    state: Mapped[GameState] = mapped_column(
        default=GameState.WAITING_FOR_PLAYERS
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.question_id")
    )
    revealed_letters: Mapped[str] = mapped_column(default="")
    current_player_id: Mapped[int | None] = mapped_column(
        ForeignKey("game_participants.participant_id", ondelete="SET NULL")
    )
    bonus_points: Mapped[int] = mapped_column(default=0)

    current_player: Mapped["GameParticipantModel"] = relationship(
        back_populates="current_game",
        foreign_keys=[current_player_id],
        lazy="joined",
        uselist=False,
    )
    question: Mapped["QuestionModel"] = relationship()
    game_participants: Mapped[list["GameParticipantModel"]] = relationship(
        back_populates="game",
        cascade="all, delete-orphan",
        foreign_keys="[GameParticipantModel.game_id]",
    )


class UserModel(BaseModel):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tg_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
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
    turn_order: Mapped[int]
    points: Mapped[int] = mapped_column(default=0)

    game: Mapped["GameModel"] = relationship(
        back_populates="game_participants",
        foreign_keys=[game_id],
    )
    current_game: Mapped["GameModel"] = relationship(
        back_populates="current_player",
        foreign_keys="[GameModel.current_player_id]",
    )
    user: Mapped["UserModel"] = relationship(
        back_populates="game_participations",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_user_game"),
    )


class QuestionModel(BaseModel):
    __tablename__ = "questions"

    question_id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(unique=True)
    answer: Mapped[str] = mapped_column(unique=True)
