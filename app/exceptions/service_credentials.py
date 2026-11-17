from app.exceptions.base import ApplicationError


class ServiceCredentialsError(ApplicationError):
    pass


class ServiceCredentialAlreadyExists(ServiceCredentialsError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "SERVICE_CREDENTIAL_ALREADY_EXISTS", 409)


class ServiceCredentialNotFound(ServiceCredentialsError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "SERVICE_CREDENTIAL_NOT_FOUND", 404)


class InvalidServiceCredntialError(ServiceCredentialsError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "SERVICE_CREDENTIAL_INVALID", 422)
