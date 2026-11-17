from app.exceptions.base import ApplicationError


class DatabaseError(ApplicationError):
    pass


class DatabaseIntegrityError(DatabaseError):
    def __init__(self, message):
        super().__init__(message, "DATABASE_INTEGRITY_ERROR", 409)


class DatabaseConnectionError(DatabaseError):
    def __init__(self, message):
        super().__init__(message, "DATABASE_CONNECTION_ERROR", 500)
