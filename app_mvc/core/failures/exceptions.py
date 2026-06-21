"""Shared domain and application exceptions."""


class AppException(Exception):
    """Base application exception carrying a user-safe message and a machine-readable code."""

    def __init__(self, message: str, code: str) -> None:
        """Initialize the exception payload used by global exception handlers."""
        ...


class UnauthorizedException(AppException):
    """Raised when the caller is not authenticated or lacks valid credentials."""


class ForbiddenException(AppException):
    """Raised when the caller is authenticated but not allowed to access the resource."""


class ResourceNotFoundException(AppException):
    """Raised when the requested domain object cannot be found."""


class ValidationException(AppException):
    """Raised when a domain-level validation rule fails."""


class ProviderException(AppException):
    """Raised when an external provider integration fails or returns an unusable response."""
