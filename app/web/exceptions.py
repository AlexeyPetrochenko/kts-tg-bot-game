class AppError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class LoadConfigError(AppError):
    pass


class AdminCreateError(AppError):
    def __init__(self, email: str) -> None:
        super().__init__(reason=f"This email: [{email}] is already taken")
        self.email = email
