class AppError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class LoadConfigError(AppError):
    pass


class GameCreateError(AppError):
    def __init__(self, chat_id: int) -> None:
        super().__init__(reason=f"Failed create game in chat [{chat_id}]")
        self.chat_id = chat_id


class QuestionCreateError(AppError):
    def __init__(self, question: str, answer: str) -> None:
        super().__init__(
            reason=f"Failed to add question [{question}] - [{answer}]"
        )
        self.question = question
        self.answer = answer


class QuestionNotFoundError(AppError):
    pass


class UserCreateError(AppError):
    def __init__(self, tg_user_id: int) -> None:
        super().__init__(reason=f"Error creating user_tg_id-[{tg_user_id}]")
        self.tg_user_id = tg_user_id


class ParticipantRegistrationError(AppError):
    def __init__(self, game_id: int, user_id: int) -> None:
        super().__init__(
            reason=f"""
            Participant id[{user_id}] is already registered
            in game id[{game_id}]
            """
        )
        self.game_id = game_id
        self.user_id = user_id


class ParticipantCreateError(AppError):
    def __init__(self, game_id: int, user_id: int) -> None:
        super().__init__(
            reason=f"error creating user_id[{user_id}] game_id[{game_id}]"
        )
        self.game_id = game_id
        self.user_id = user_id
