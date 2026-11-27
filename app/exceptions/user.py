from app.exceptions.base import ApplicationError


class UserNotFoundError(ApplicationError):
    def __init__(self, message: str = "User not found"):
        super().__init__(message, "USER_NOT_FOUND", 404)


class UserAlreadyExistsError(ApplicationError):
    def __init__(self, message: str = "User already exists"):
        super().__init__(message, "USER_ALREADY_EXISTS", 409)


class UserInactiveError(ApplicationError):
    def __init__(self, message: str = "User account is inactive"):
        super().__init__(message, "USER_INACTIVE", 403)
