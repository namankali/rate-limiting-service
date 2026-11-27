from app.exceptions.base import ApplicationError


class InvalidLoginError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            "Invalid email or password",
            "INVALID_LOGIN",
            401,
        )


class InvalidSessionError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            "Session is invalid, expired or revoked",
            "INVALID_SESSION",
            401,
        )


class InactiveUserError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            "User account is inactive",
            "USER_INACTIVE",
            403,
        )
