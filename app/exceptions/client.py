from app.exceptions.base import ApplicationError


class ClientError(ApplicationError):
    pass


class ClientNotFoundError(ClientError):
    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(message, "CLIENT_NOT_FOUND", 404)


class ClientInactiveError(ClientError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "CLIENT_INACTIVE", 403)


class ClientAlreadyExistsError(ClientError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "CLIENT_ALREADY_EXISTS", 409)
