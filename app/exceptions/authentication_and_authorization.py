from app.exceptions.base import ApplicationError


class AuthenticationError(ApplicationError):
    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "AUTHENTICATION_ERROR",
        status_code: int = 401,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
        )


class AuthorizationError(ApplicationError):
    def __init__(
        self,
        message: str = "Insufficient permissions",
        error_code: str = "AUTHORIZATION_ERROR",
        status_code: int = 403,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
        )
