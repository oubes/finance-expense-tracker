# ---------- core/exceptions.py ----------


class BaseAPIException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "internal_error",
        details: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


# ---------- 4xx Client Errors ----------

class ValidationException(BaseAPIException):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="validation_error",
            details=details,
        )


class UnauthorizedException(BaseAPIException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="unauthorized",
        )


class ForbiddenException(BaseAPIException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="forbidden",
        )


class NotFoundException(BaseAPIException):
    def __init__(self, message: str = "Not found"):
        super().__init__(
            message=message,
            status_code=404,
            error_code="not_found",
        )


# ---------- 5xx System Errors ----------

class ServiceUnavailableException(BaseAPIException):
    def __init__(self, service: str):
        super().__init__(
            message=f"{service} service is unavailable",
            status_code=503,
            error_code="service_unavailable",
        )


class ExternalServiceException(BaseAPIException):
    def __init__(self, service: str, message: str = "External service failed"):
        super().__init__(
            message=f"{service}: {message}",
            status_code=502,
            error_code="external_service_error",
        )


class TimeoutException(BaseAPIException):
    def __init__(self, service: str):
        super().__init__(
            message=f"{service} timeout",
            status_code=504,
            error_code="timeout",
        )


class InternalServerException(BaseAPIException):
    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            message=message,
            status_code=500,
            error_code="internal_error",
        )