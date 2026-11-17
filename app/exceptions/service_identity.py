from app.exceptions.base import ApplicationError


class ServiceIdentityError(ApplicationError):
    pass


class ServiceIdentityAlreadyExists(ServiceIdentityError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "SERVICE_IDENTITY_ALREADY_EXISTS", 409)


class ServiceIdentityNotFound(ServiceIdentityError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "SERVICE_IDENTITY_NOT_FOUND", 404)


class InvalidServiceIdentityError(ServiceIdentityError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "SERVICE_IDENTITY_INVALID", 422)
